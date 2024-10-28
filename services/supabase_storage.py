from supabase import create_client
import os
import logging
import time

class SupabaseStorage:
    def __init__(self):
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials")
            
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = 'audio-chunks'
        
    def upload_audio_chunk(self, audio_data, filename):
        try:
            # Try to upload directly without checking bucket
            try:
                # Upload the audio chunk to Supabase storage
                self.supabase.storage.from_(self.bucket_name).upload(
                    path=filename,
                    file=audio_data,
                    file_options={"content-type": "audio/wav"}
                )
            except Exception as upload_error:
                if "bucket not found" in str(upload_error).lower():
                    # If bucket doesn't exist, try to create it and retry upload
                    try:
                        self.supabase.storage.create_bucket(
                            self.bucket_name,
                            options={'public': True}
                        )
                        time.sleep(1)  # Give some time for bucket creation to propagate
                        # Retry upload
                        self.supabase.storage.from_(self.bucket_name).upload(
                            path=filename,
                            file=audio_data,
                            file_options={"content-type": "audio/wav"}
                        )
                    except Exception as bucket_error:
                        logging.error(f"Error creating bucket: {str(bucket_error)}")
                        return None
                else:
                    raise upload_error
            
            # Get the public URL for the uploaded file
            file_url = self.supabase.storage.from_(self.bucket_name).get_public_url(filename)
            return file_url
            
        except Exception as e:
            logging.error(f"Error uploading audio chunk: {str(e)}")
            return None

    def delete_audio_chunk(self, filename):
        try:
            self.supabase.storage.from_(self.bucket_name).remove([filename])
            return True
        except Exception as e:
            logging.error(f"Error deleting audio chunk: {str(e)}")
            return False
