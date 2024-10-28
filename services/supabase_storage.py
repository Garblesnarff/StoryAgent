from supabase import create_client
import os
import logging
import time
from datetime import datetime

class SupabaseStorage:
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = 'audio'  # Using a simpler bucket name
        
        # Initialize bucket
        self._initialize_bucket()
    
    def _initialize_bucket(self, max_retries=3):
        """Initialize storage bucket with retry mechanism"""
        for attempt in range(max_retries):
            try:
                # Check if bucket exists
                buckets = self.supabase.storage.list_buckets()
                bucket_exists = any(
                    bucket.get('name') == self.bucket_name 
                    for bucket in buckets if isinstance(bucket, dict)
                )

                if not bucket_exists:
                    try:
                        # Create bucket
                        self.supabase.storage.create_bucket(self.bucket_name)
                        logging.info(f"Created new bucket: {self.bucket_name}")
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            logging.info(f"Bucket {self.bucket_name} already exists")
                            pass
                        else:
                            raise
                
                # Verify bucket access
                self.supabase.storage.from_(self.bucket_name).list()
                logging.info(f"Successfully verified access to bucket: {self.bucket_name}")
                return
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Failed to initialize bucket after {max_retries} attempts: {str(e)}")
                    raise
                logging.warning(f"Bucket initialization attempt {attempt + 1} failed: {str(e)}, retrying...")
                time.sleep(1)

    def upload_audio_chunk(self, audio_data, filename):
        """Upload audio data to Supabase storage"""
        try:
            # Convert audio_data to bytes if needed
            if isinstance(audio_data, bytearray):
                audio_data = bytes(audio_data)
            
            # Add timestamp to filename for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_with_timestamp = f"{timestamp}_{filename}"
            
            # Upload with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Upload file with content type
                    result = self.supabase.storage \
                        .from_(self.bucket_name) \
                        .upload(
                            path=filename_with_timestamp,
                            file=audio_data,
                            file_options={"contentType": "audio/wav"}
                        )
                    
                    if result:
                        # Get public URL
                        file_url = self.supabase.storage \
                            .from_(self.bucket_name) \
                            .get_public_url(filename_with_timestamp)
                        
                        logging.info(f"Successfully uploaded audio file: {filename_with_timestamp}")
                        return file_url
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Failed to upload audio after {max_retries} attempts: {str(e)}")
                        raise
                    logging.warning(f"Upload attempt {attempt + 1} failed: {str(e)}, retrying...")
                    time.sleep(1)
            
            return None
                
        except Exception as e:
            logging.error(f"Error uploading audio chunk: {str(e)}")
            return None
    
    def delete_audio_chunk(self, filename):
        """Delete an audio file from storage"""
        try:
            self.supabase.storage \
                .from_(self.bucket_name) \
                .remove([filename])
            logging.info(f"Successfully deleted audio file: {filename}")
            return True
        except Exception as e:
            logging.error(f"Error deleting audio chunk: {str(e)}")
            return False
