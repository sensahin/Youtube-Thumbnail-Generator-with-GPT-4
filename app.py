from flask import Flask, request, render_template
from selenium import webdriver
from openai import OpenAI
import boto3
import time
import requests
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Replace with your actual OpenAI API key and AWS credentials
            openai_api_key = ''
            aws_access_key_id = ''
            aws_secret_access_key = ''
            s3_bucket_name = ''

            # Initialize OpenAI client
            client = OpenAI(api_key=openai_api_key)
            fullurl = request.form['youtube_url']

            # Selenium WebDriver setup
            op = webdriver.ChromeOptions()
            op.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36")
            op.add_argument('headless')
            driver = webdriver.Chrome(options=op)
            driver.get(fullurl)
            time.sleep(5)

            # Take a screenshot and save it in the current directory
            screenshot_filename = 'screenshot.png'
            driver.save_screenshot(screenshot_filename)
            driver.quit()

            # Initialize boto3 client
            s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

            # Upload the screenshot to S3
            s3_client.upload_file(screenshot_filename, s3_bucket_name, screenshot_filename)
            pre_signed_url = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': s3_bucket_name, 'Key': screenshot_filename},
                                                            ExpiresIn=60)

            # Analyze the image using OpenAI's GPT-Vision
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What’s in this image? Respond in English."},
                            {"type": "image_url", "image_url": pre_signed_url},
                        ],
                    }
                ],
                max_tokens=300,
            )

            # Extract prompt from response
            description = response.choices[0].message.content
            thumbnail_prompt = f"Create a YouTube thumbnail image that visually represents this scene: {description}. The image should be vibrant, engaging, and suitable for a YouTube audience, including bold text elements and a compelling composition."


            # Request DALL-E to generate an image
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openai_api_key}'
            }
            data = json.dumps({
                "model": "dall-e-3",
                "quality": "hd",
                "prompt": thumbnail_prompt, 
                "n": 1,
                "style": "vivid",
                "size": "1024x1024"
            })
            response = requests.post('https://api.openai.com/v1/images/generations', headers=headers, data=data)
            if response.status_code == 200:
                image_url = response.json()['data'][0]['url']
                return render_template('result.html', image_url=image_url)
            else:
                error_message = "Error in generating image with DALL-E"
                return render_template('error.html', message=error_message)
        except Exception as e:
            # Log the exception or display it in a user-friendly way
            return render_template('error.html', message=str(e))
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
