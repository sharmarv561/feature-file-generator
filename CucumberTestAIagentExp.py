import boto3
import botocore.config
import json
from datetime import datetime
import logging
import uuid
import mimetypes
import os
from email.mime.multipart import MIMEMultipart  # Importing MIMEMultipart
from email.mime.text import MIMEText  # Importing MIMEText for text and HTML parts
from email.mime.base import MIMEBase  # Importing MIMEBase for file attachments
from email import encoders


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# NEW: Configure clients with timeouts
bedrock_config = botocore.config.Config(
    connect_timeout=20,    # NEW: Explicit timeout settings
    read_timeout=20,
    retries={'max_attempts': 2}
)

s3_config = botocore.config.Config(
    connect_timeout=20,
    read_timeout=20,
    retries={'max_attempts': 2}
)

# NEW: Initialize clients outside the handler for better performance
bedrock_client = boto3.client("bedrock-runtime", 
                            region_name="us-east-1",
                            config=bedrock_config)

s3_client = boto3.client('s3', 
                        region_name="us-east-1",
                        config=s3_config)

ses_client = boto3.client('ses', region_name='us-east-1', config=s3_config) 

def testfile_generator(promtMessage: str) -> str:
    try:
        # Define the request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8000,
            "temperature": 1,
            "top_p": 0.999,
            "messages": [
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": promtMessage
                    }
                    ]
                }
            ]
        }

        logger.info(f"Attempting to generate test cases for prompt: {promtMessage}")
        logger.info(f"Request body: {json.dumps(body)}")

        # Create a Bedrock Runtime client
        client = boto3.client("bedrock-runtime", region_name="us-east-1")

        # Invoke the Jurassic-2 Mid model
        response = bedrock_client.invoke_model(
            modelId="us.anthropic.claude-3-5-haiku-20241022-v1:0",  # Correct inference profile ID for claude 3.5 haiku
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        logger.info(f"Raw response: {response_body}")

        # Extract the generated story
        test_cases = response_body["content"][0]["text"]
        if test_cases:
            logger.info(f"Test case generation completed. Length: {len(test_cases)}")
            # Parse the response
            logger.info(f"Successfully generated test cases: {test_cases[:100]}...")
            return test_cases
        else:
            logger.error("No test cases was generated in the response.")
            return ""

    except botocore.exceptions.ClientError as e:
        # IMPROVED: More specific error handling
        logger.error(f"Bedrock API error: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in story generation: {str(e)}")
        raise

def save_to_s3(text_content: str, s3_bucket: str) -> dict:
    """
    Save text content to S3 bucket as a .txt file
    """
    try:
        # Create S3 client with specific configuration
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_id = str(uuid.uuid4())[:8]
        s3_key = f"testFile/{timestamp}_{file_id}.txt"

        logger.info(f"Attempting to save file to S3: {s3_key}")
        logger.info(f"Bucket: {s3_bucket}")
        logger.info(f"Content length: {len(text_content)}")

        # Encode content
        text_content_bytes = text_content.encode('utf-8')

        # CHANGED: Using pre-initialized client
        response = s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=text_content_bytes,
            ContentType='text/plain',
            Metadata={
                'timestamp': timestamp,
                'generator': 'lambda-bedrock'
            }
        )

        logger.info(f"S3 upload response: {response}")

        # Verify upload success
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {
                "success": True,
                "message": "File saved successfully",
                "file_location": f"s3://{s3_bucket}/{s3_key}",
                "s3_key": s3_key
            }
        else:
            raise Exception(f"S3 upload failed with response: {response}")

    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS S3 error: {error_code} - {error_message}")
        logger.error(f"Full error: {str(e)}")
        return {
            "success": False,
            "error": f"S3 error: {error_code} - {error_message}"
        }
    except Exception as e:
        logger.error(f"Unexpected error saving to S3: {str(e)}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

def send_email_with_attachment(bucket_name, file_name, recipient_email) -> dict:
    sender = "info@adwicorp.com"  # Sender email (must be verified in SES)
    recipient = recipient_email  # Recipient email
    reply_to_email = "sharmarv561@gmail.com"  # Different reply-to email
    subject = "AI-Powered Test Case Generation | Resume & GitHub Link Attached"

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.add_header("Reply-To", reply_to_email)

    # Create alternative MIME structure (Text + HTML)
    msg_alternative = MIMEMultipart("alternative")

    # Add plain text version (fallback)
    body_text = "Please find the attached files."
    msg_alternative.attach(MIMEText(body_text, "plain"))

    # Read HTML content from the txt file in S3
    email_html_content_file = "cucumber_test_case_email_content.txt"
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=email_html_content_file)
        file_content = response["Body"].read().decode("utf-8")

        # Add HTML version
        msg_alternative.attach(MIMEText(file_content, "html"))
    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"AWS S3 error for file {email_html_content_file}: {error_code} - {error_message}")
        return {"success": False, "error": f"S3 error: {error_code} - {error_message}"}
    except Exception as e:
        logger.error(f"Error reading HTML file from S3: {str(e)}")
        return {"success": False, "error": f"Error reading HTML file from S3: {str(e)}"}

    # Attach the alternative MIME part (Text + HTML)
    msg.attach(msg_alternative)

    # Attach additional files from S3
    resume_path = "ROHIT_SHARMA_TEST_AUTOMATION_ENGINEER_5_Years.pdf"
    file_paths = [resume_path, file_name]
    for file_path in file_paths:
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=file_path)
            file_content = response["Body"].read()

            # Guess MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Create attachment
            attachment = MIMEBase(*mime_type.split("/"))
            attachment.set_payload(file_content)
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
            msg.attach(attachment)

        except botocore.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logger.error(f"AWS S3 error for file {file_path}: {error_code} - {error_message}")
            return {"success": False, "error": f"S3 error: {error_code} - {error_message}"}
        except Exception as e:
            logger.error(f"Error retrieving file {file_path} from S3: {str(e)}")
            return {"success": False, "error": f"Error retrieving file {file_path}: {str(e)}"}

    # Send the email using SES
    try:
        response = ses_client.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={"Data": msg.as_string()}
        )

        logger.info(f"Email sent response: {response}")

        if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            return {"success": True, "message": "Email sent successfully with multiple attachments"}
        else:
            raise Exception(f"Email sending failed: {response}")

    except botocore.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"AWS SES error: {error_code} - {error_message}")
        return {"success": False, "error": f"SES error: {error_code} - {error_message}"}

    except Exception as e:
        logger.error(f"Unexpected error while sending email: {str(e)}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def lambda_handler(event, context):
    #logger.info(f"Received event: {event}")

    try:
        # Handle both string and dict body
        if isinstance(event['body'], str):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse request body: {str(e)}")
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                           'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Invalid JSON in request body',
                        'details': str(e)
                    })
                }
        else:
            body = event['body']
        logger.info(f"Received event: {body.get('body')}")
        # Validate story_topic
        promtMessage = body.get('body').get('prompt_messsage')
        # Extract and minify open_api_spec
        open_api_spec_minified = json.dumps(body.get('open_api_spec'), separators=(",", ":"))

        # Concatenate promtMessage and open_api_spec_minified
        concatenated_message = promtMessage + open_api_spec_minified

        if not concatenated_message:
            logger.error("Missing promt message in request")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                       'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Missing story_topic in request'
                })
            }

        # Generate story
        test_cases = testfile_generator(promtMessage=concatenated_message)
        #test_cases = concatenated_message
        if not test_cases:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json',   'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Story generation failed'})
            }
        if test_cases:
            s3_bucket = 'cucumber-feature-file'

            # Save to S3
            s3_response = save_to_s3(test_cases, s3_bucket)
            if not s3_response['success']:
                logger.error(f"Failed to save to S3: {s3_response.get('error')}")
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                           'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': f"Failed to save story to S3: {s3_response.get('error')}",
                        'story': test_cases
                    })
                }
            
            # #send email
            # ses_response = send_email_with_attachment(s3_bucket, s3_response['s3_key'], body.get('recipient-email'))
            # if not ses_response['success']:
            #     logger.error(f"Failed to send email: {ses_response.get('error')}")
            #     return {
            #         'statusCode': 500,
            #         'headers': {
            #             'Content-Type': 'application/json',
            #                'Access-Control-Allow-Origin': '*'
            #         },
            #         'body': json.dumps({
            #             'error': f"Failed to send email: {ses_response.get('error')}",
            #             'story': test_cases
            #         })
            #     }

            # Success response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                       'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'message': 'Test cases generated and saved successfully',
                    'test_cases': test_cases,
                    's3_location': s3_response['file_location']
                })
            }
    
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                   'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        }