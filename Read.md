Cucumber Test Case Generator with Claude Haiku 3.5 and Open API Spec Integration

This project demonstrates how to set up a system that uses AWS Lambda to generate Cucumber test cases based on a given Open API specification. The system leverages Claude Haiku 3.5 from Anthropic to generate the test cases automatically, with integration to S3 for storage and email notifications for completion alerts. The Lambda function is designed to process API specifications, create detailed test cases, and store them efficiently while managing any potential errors during execution.

Prerequisites

Before setting up the environment, ensure you have the following:

1. AWS Account: An active AWS account with access to the following services:
- AWS Lambda
- Amazon S3
- AWS Bedrock
- AWS Identity and Access Management (IAM)

2. AWS CLI: Installed and configured with credentials that have the necessary permissions.
- Install AWS CLI

3. Python: Python 3.9 or later installed locally for testing and packaging the Lambda function.

4. IAM Permissions:
- Ensure the Lambda execution role has the following permissions:
    bedrock:InvokeModel for invoking the Claude Haiku 3.5 model.
    s3:PutObject, s3:GetObject for saving files to the S3 bucket.
    ses:send_raw_email for sending email
    logs:CreateLogGroup, logs:CreateLogStream, and logs:PutLogEvents for CloudWatch logging.

Setup Instructions:

1.1 Create an AWS Lambda Function

- Go to the AWS Lambda Console: AWS Lambda Console.
- Create a New Function:
    Choose Author from Scratch.
    Set the Function Name (e.g., CucumberTestCaseGenerator).
    Choose Runtime: Python 3.x (or Node.js, depending on your implementation).
    Choose an Execution Role: Create a new role with basic Lambda permissions (allowing s3:PutObject and bedrock:InvokeModel actions).
- Click Create Function.

1.2 Configure Lambda Execution Role Permissions
- Attach the following permissions to your Lambda execution role to interact with AWS S3 and Bedrock:
    S3 permissions (s3:PutObject for your S3 bucket).
    Bedrock permissions (bedrock:InvokeModel for invoking Claude Haiku 3.5).

1.3 Lambda Function Code
- Edit the Lambda Code:
    In the Lambda console, paste the python code into the Lambda function editor.

2. Set Up the S3 Bucket
- Go to the AWS S3 Console: AWS S3 Console.
- Create a New Bucket:
    Choose a unique name for your bucket.
    Set the region and other configuration options (leave default for now).
- Ensure the Lambda execution role has the s3:PutObject, s3:GetObject permission for this bucket.

3. Sending Email Notifications
You can use AWS SNS or AWS SES to send email notifications upon successful upload. Here's how you can set up email notifications using SNS:
- Go to the SNS Console: SNS Console.
- Create a Topic:
    Create a new SNS topic (e.g., TestCaseGenerationNotifications).
- Create a Subscription:
    Add an email subscription to the topic (enter your email address).
- In your Lambda function, add the code to publish a message to SNS after the S3 upload:

4. Running the Project
- Invoke the Lambda Function
    Use the AWS Lambda console to trigger the function manually or via an event.
    You can trigger the Lambda using an API Gateway or an automated CI/CD pipeline.
- Input Open API Specification
    When invoking the Lambda function, ensure the Open API specification is provided in the input event payload. For example:

5. View Generated Test Cases
Once the Lambda function completes:
- Go to the S3 bucket.
- Find the txt file inside testFile folder.
- Open the file to view the generated Cucumber test cases.