# Show Messages and Plot Images in Financial Analysis If ANY

import os
# import requests
# from IPython.display import Image, display
from openai.types.beta.threads import ThreadMessage

def delete_file(file_path : str) -> None:
    """Delete a file at the specified path."""
    try:
        os.remove(file_path)
        print(f"File {file_path} has been deleted successfully.")
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except PermissionError:
        print(f"Permission denied: unable to delete {file_path}.")
    except Exception as e:
        print(f"Error occurred while deleting file {file_path}: {e}")

# def download_and_save_image(file_id: str, save_path: str) -> None:
#     """
#     Downloads an image from OpenAI using its file ID and saves it to the specified path.

#     Args:
#     - file_id (str): The ID of the file to download.
#     - save_path (str): The path where the image will be saved.

#     Returns:
#     - None
#     """
#     # Construct the URL to download the image
#     download_url = f"https://api.openai.com/v1/files/{file_id}/content"

#     # Perform the HTTP GET request to download the image
#     response = requests.get(download_url, headers={"Authorization": f"Bearer {os.environ.get("OPENAI_API_KEY")}"})

#     # Check if the request was successful
#     if response.status_code == 200:
#         # Write the image to the specified file
#         with open(save_path, 'wb') as file:
#             file.write(response.content)
#         print(f"Image downloaded and saved to {save_path}")
#     else:
#         print(f"Failed to download image: HTTP Status Code {response.status_code}")


def pretty_print(messages: list[ThreadMessage]) -> None:
    print("# Messages")
    for message in messages:
        role_label = "User" if message.role == "user" else "Assistant"
        # Check the type of message content and handle accordingly
        for content in message.content:
            if content.type == "text":
                message_content = content.text.value
                print(f"{role_label}: {message_content}\n")
                print()
            elif content.type == "image_file":
                print("Found an Image Generated")
                # Handle image file content, e.g., print the file ID or download the image
                # image_file_id = content.image_file.file_id
                # Define a path to save the image
                # image_save_path = f"image_{image_file_id}.png"
                # Download and save the image
                # print(f"{role_label}: Image file ID: {image_file_id}")
                # download_and_save_image(image_file_id, image_save_path)

                # Display the image within Jupyter Notebook
                # display(Image(filename=image_save_path))