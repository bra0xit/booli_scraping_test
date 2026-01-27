import os
import requests
from urllib.parse import urlparse
import hashlib
from datetime import datetime


class ImageManager:
    """Manager for downloading and organizing listing images"""

    def __init__(self, base_path='data/images'):
        """
        Initialize image manager

        Args:
            base_path: Base directory for storing images
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def get_listing_image_dir(self, hemnet_id):
        """
        Get the image directory for a specific listing

        Args:
            hemnet_id: Hemnet listing ID

        Returns:
            Path to the listing's image directory
        """
        listing_dir = os.path.join(self.base_path, str(hemnet_id))
        os.makedirs(listing_dir, exist_ok=True)
        return listing_dir

    def download_image(self, image_url, hemnet_id, image_order=0):
        """
        Download an image from URL and save locally

        Args:
            image_url: URL of the image to download
            hemnet_id: Hemnet listing ID
            image_order: Order/index of the image in the listing

        Returns:
            Local file path if successful, None otherwise
        """
        try:
            # Get listing directory
            listing_dir = self.get_listing_image_dir(hemnet_id)

            # Parse image URL to get extension
            parsed_url = urlparse(image_url)
            path = parsed_url.path
            extension = os.path.splitext(path)[1] or '.jpg'

            # Create filename: image_001.jpg, image_002.jpg, etc.
            filename = f"image_{image_order:03d}{extension}"
            local_path = os.path.join(listing_dir, filename)

            # Download image
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Save image
            with open(local_path, 'wb') as f:
                f.write(response.content)

            print(f"  Downloaded image {image_order + 1}: {filename}")

            # Return relative path (relative to backend directory)
            return os.path.relpath(local_path, start=os.path.dirname(os.path.dirname(__file__)))

        except Exception as e:
            print(f"  Error downloading image from {image_url}: {e}")
            return None

    def download_all_images(self, hemnet_id, image_urls):
        """
        Download all images for a listing

        Args:
            hemnet_id: Hemnet listing ID
            image_urls: List of image URLs

        Returns:
            List of local file paths
        """
        local_paths = []

        print(f"Downloading {len(image_urls)} images for listing {hemnet_id}...")

        for idx, url in enumerate(image_urls):
            local_path = self.download_image(url, hemnet_id, idx)
            local_paths.append(local_path)

        successful = sum(1 for path in local_paths if path is not None)
        print(f"Successfully downloaded {successful}/{len(image_urls)} images")

        return local_paths

    def get_image_path(self, hemnet_id, image_order=0, extension='.jpg'):
        """
        Get the expected path for an image

        Args:
            hemnet_id: Hemnet listing ID
            image_order: Order of the image
            extension: File extension

        Returns:
            Expected file path
        """
        listing_dir = self.get_listing_image_dir(hemnet_id)
        filename = f"image_{image_order:03d}{extension}"
        return os.path.join(listing_dir, filename)

    def image_exists(self, hemnet_id, image_order=0):
        """
        Check if an image has already been downloaded

        Args:
            hemnet_id: Hemnet listing ID
            image_order: Order of the image

        Returns:
            True if image file exists, False otherwise
        """
        listing_dir = self.get_listing_image_dir(hemnet_id)

        # Check common image extensions
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            filename = f"image_{image_order:03d}{ext}"
            if os.path.exists(os.path.join(listing_dir, filename)):
                return True

        return False

    def get_listing_images(self, hemnet_id):
        """
        Get all downloaded images for a listing

        Args:
            hemnet_id: Hemnet listing ID

        Returns:
            List of image file paths
        """
        listing_dir = self.get_listing_image_dir(hemnet_id)

        if not os.path.exists(listing_dir):
            return []

        # Get all image files and sort by name
        images = []
        for filename in sorted(os.listdir(listing_dir)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                images.append(os.path.join(listing_dir, filename))

        return images

    def delete_listing_images(self, hemnet_id):
        """
        Delete all images for a listing

        Args:
            hemnet_id: Hemnet listing ID

        Returns:
            Number of images deleted
        """
        listing_dir = self.get_listing_image_dir(hemnet_id)

        if not os.path.exists(listing_dir):
            return 0

        count = 0
        for filename in os.listdir(listing_dir):
            file_path = os.path.join(listing_dir, filename)
            try:
                os.remove(file_path)
                count += 1
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        # Try to remove the directory
        try:
            os.rmdir(listing_dir)
        except:
            pass

        return count

    def get_storage_stats(self):
        """
        Get storage statistics

        Returns:
            Dictionary with storage stats
        """
        total_images = 0
        total_size = 0
        listings_with_images = 0

        if not os.path.exists(self.base_path):
            return {
                'total_images': 0,
                'total_size_mb': 0,
                'listings_with_images': 0
            }

        # Count images and calculate size
        for listing_dir in os.listdir(self.base_path):
            listing_path = os.path.join(self.base_path, listing_dir)

            if os.path.isdir(listing_path):
                images = [f for f in os.listdir(listing_path)
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]

                if images:
                    listings_with_images += 1
                    total_images += len(images)

                    for img in images:
                        img_path = os.path.join(listing_path, img)
                        try:
                            total_size += os.path.getsize(img_path)
                        except:
                            pass

        return {
            'total_images': total_images,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'listings_with_images': listings_with_images
        }
