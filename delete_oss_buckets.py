#!/usr/bin/env python3
import oss2
import sys
import os
from typing import List, Dict

class OSSBucketDeleter:
    def __init__(self, access_key_id: str = None, access_key_secret: str = None):
        # Read from environment if not provided
        self.access_key_id = access_key_id or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_ID')
        self.access_key_secret = access_key_secret or os.getenv('ALIBABA_CLOUD_ACCESS_KEY_SECRET')
        
        if not self.access_key_id or not self.access_key_secret:
            raise ValueError("Credentials not found. Set environment variables or pass as arguments.")
        
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        # Use global endpoint to list all buckets
        self.service = oss2.Service(self.auth, 'https://oss-cn-hangzhou.aliyuncs.com')
    
    def list_buckets(self) -> Dict[str, str]:
        """List all buckets with their regions"""
        try:
            result = self.service.list_buckets()
            buckets = {}
            for bucket in result.buckets:
                # Get bucket region
                try:
                    bucket_obj = oss2.Bucket(self.auth, 'https://oss-cn-hangzhou.aliyuncs.com', bucket.name)
                    bucket_info = bucket_obj.get_bucket_info()
                    region = bucket_info.location
                    # Clean region name for display
                    clean_region = region.replace('oss-', '') if region.startswith('oss-') else region
                    buckets[bucket.name] = clean_region
                except Exception as e:
                    print(f"Warning: Could not get region for {bucket.name}: {e}")
                    buckets[bucket.name] = 'unknown'
            return buckets
        except Exception as e:
            print(f"Error listing buckets: {e}")
            return {}
    
    def empty_bucket(self, bucket_name: str, endpoint: str) -> bool:
        """Delete all objects in a bucket"""
        try:
            bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            
            # Delete all objects
            for obj in oss2.ObjectIterator(bucket):
                bucket.delete_object(obj.key)
            
            # Delete all multipart uploads
            result = bucket.list_multipart_uploads()
            for upload in result.upload_list:
                bucket.abort_multipart_upload(upload.key, upload.upload_id)
            
            return True
        except Exception as e:
            print(f"Error emptying bucket {bucket_name}: {e}")
            return False
    
    def delete_access_points(self, bucket_name: str, endpoint: str) -> bool:
        """Delete all access points for a bucket"""
        try:
            bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            
            # Clear bucket configurations first
            try:
                bucket.delete_bucket_lifecycle()
                print(f"    Cleared lifecycle rules")
            except:
                pass
            
            try:
                bucket.delete_bucket_cors()
                print(f"    Cleared CORS rules")
            except:
                pass
            
            try:
                bucket.delete_bucket_website()
                print(f"    Cleared website config")
            except:
                pass
            
            # Try using OSS2 internal methods for access points
            try:
                # Use the service object to make raw API calls
                service = oss2.Service(self.auth, endpoint)
                
                # Try to get access points using raw HTTP request
                from oss2.api import _make_range_string
                from oss2 import http
                
                # Make direct API call to list access points
                resp = service._Service__do('GET', bucket_name, {'accessPoint': ''}, None)
                
                if resp.status == 200:
                    # Parse response to extract access point names
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.read())
                    
                    # Find access points in XML
                    for ap_elem in root.iter():
                        if ap_elem.tag.endswith('Name') and ap_elem.getparent() and ap_elem.getparent().tag.endswith('AccessPoint'):
                            ap_name = ap_elem.text
                            if ap_name:
                                # Delete the access point
                                try:
                                    del_resp = service._Service__do('DELETE', bucket_name, {'accessPoint': '', 'name': ap_name}, None)
                                    if del_resp.status in [200, 204]:
                                        print(f"    Deleted access point: {ap_name}")
                                    else:
                                        print(f"    Failed to delete access point {ap_name}")
                                except Exception as del_e:
                                    print(f"    Error deleting access point {ap_name}: {del_e}")
                    
                    return True
                else:
                    print(f"    Could not list access points: {resp.status}")
                    return False
                    
            except Exception as api_e:
                print(f"    Access point API not available: {api_e}")
                # Skip access point deletion if API not available
                return True
                
        except Exception as e:
            print(f"    Error handling bucket dependencies: {e}")
            return False
    
    def delete_bucket(self, bucket_name: str, endpoint: str) -> bool:
        """Delete a single bucket"""
        try:
            bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
            bucket.delete_bucket()
            return True
        except Exception as e:
            error_str = str(e)
            if 'BucketBindingAccessPoints' in error_str or 'BucketNotEmpty' in error_str:
                print(f"  Bucket has dependencies, clearing configurations...")
                if self.delete_access_points(bucket_name, endpoint):
                    # Try deleting bucket again
                    try:
                        bucket.delete_bucket()
                        return True
                    except Exception as e2:
                        print(f"  Still cannot delete bucket: {e2}")
                        print(f"  ⚠️  SKIPPING - Manual cleanup required in console")
                        print(f"      Bucket '{bucket_name}' has access points that must be removed manually")
                        return False
                else:
                    return False
            else:
                print(f"  Error deleting bucket {bucket_name}: {e}")
                return False
    
    def process_bucket(self, bucket_name: str) -> bool:
        """Process a single bucket (empty and delete)"""
        print(f"\nProcessing bucket: {bucket_name}")
        
        # Get bucket location to determine endpoint
        try:
            bucket_info = oss2.Bucket(self.auth, self.service.endpoint, bucket_name).get_bucket_info()
            region = bucket_info.location
            # Remove 'oss-' prefix if it exists in region
            clean_region = region.replace('oss-', '') if region.startswith('oss-') else region
            endpoint = f"https://oss-{clean_region}.aliyuncs.com"
        except Exception as e:
            print(f"Error getting bucket info for {bucket_name}: {e}")
            return False
        
        print(f"  Region: {clean_region}")
        
        # Empty the bucket first
        if self.empty_bucket(bucket_name, endpoint):
            print(f"  ✓ Emptied bucket {bucket_name}")
        else:
            print(f"  ✗ Failed to empty bucket {bucket_name}")
            return False
        
        # Delete the bucket
        if self.delete_bucket(bucket_name, endpoint):
            print(f"  ✓ Deleted bucket {bucket_name}")
            return True
        else:
            print(f"  ✗ Failed to delete bucket {bucket_name}")
            print(f"    ⚠️  SKIPPED - Manual cleanup required in console")
            return False
    
    def interactive_delete(self) -> None:
        """Interactive bucket deletion with numbered selection"""
        buckets = self.list_buckets()
        
        if not buckets:
            print("No buckets found.")
            return
        
        print("\n⚠️  WARNING: This operation is IRREVERSIBLE!")
        print("⚠️  All bucket data will be permanently deleted!")
        
        print(f"\nFound {len(buckets)} buckets across all regions:")
        bucket_list = list(buckets.keys())
        for i, bucket_name in enumerate(bucket_list, 1):
            region = buckets[bucket_name]
            print(f"  {i}. {bucket_name} (region: {region})")
        
        print(f"\n  0. Delete ALL buckets")
        
        try:
            choice = input("\nEnter number to delete (or 'q' to quit): ").strip()
            
            if choice.lower() == 'q':
                print("Operation cancelled.")
                return
            
            choice_num = int(choice)
            
            if choice_num == 0:
                # Delete all buckets
                print(f"\n⚠️  You are about to DELETE ALL {len(buckets)} buckets and their contents!")
                confirm = input(f"Type 'DELETE ALL' to confirm: ")
                if confirm == 'DELETE ALL':
                    failed_buckets = []
                    for i, bucket_name in enumerate(bucket_list, 1):
                        print(f"\n--- Processing {i}/{len(bucket_list)} ---")
                        success = self.process_bucket(bucket_name)
                        if not success:
                            failed_buckets.append(bucket_name)
                    
                    if failed_buckets:
                        print(f"\n⚠️  {len(failed_buckets)} bucket(s) require manual cleanup:")
                        for fb in failed_buckets:
                            print(f"   - {fb}")
                        print(f"\nPlease remove access points manually in Alibaba Cloud console")
                else:
                    print("Operation cancelled.")
            elif 1 <= choice_num <= len(bucket_list):
                # Delete specific bucket
                bucket_name = bucket_list[choice_num - 1]
                region = buckets[bucket_name]
                print(f"\n⚠️  You are about to DELETE bucket '{bucket_name}' and all its contents!")
                confirm = input(f"Type 'DELETE' to confirm: ")
                if confirm == 'DELETE':
                    success = self.process_bucket(bucket_name)
                    if not success:
                        print(f"\n⚠️  Bucket '{bucket_name}' requires manual cleanup in console")
                else:
                    print("Operation cancelled.")
            else:
                print("Invalid selection.")
                
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")

def main():
    try:
        if len(sys.argv) == 3:
            # Credentials provided as arguments
            access_key_id = sys.argv[1]
            access_key_secret = sys.argv[2]
            deleter = OSSBucketDeleter(access_key_id, access_key_secret)
        elif len(sys.argv) == 1:
            # Read from environment variables
            deleter = OSSBucketDeleter()
        else:
            print("Usage:")
            print("  python delete_oss_buckets.py <access_key_id> <access_key_secret>")
            print("  OR set environment variables:")
            print("    export ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id")
            print("    export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret")
            print("    python delete_oss_buckets.py")
            sys.exit(1)
        
        deleter.interactive_delete()
        
    except ValueError as e:
        print(f"Error: {e}")
        print("\nSet environment variables:")
        print("  export ALIBABA_CLOUD_ACCESS_KEY_ID=your_key_id")
        print("  export ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_key_secret")
        sys.exit(1)

if __name__ == "__main__":
    main()