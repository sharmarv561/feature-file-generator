# ai_generated_cucumber_test_cases

Cucumber Test Case Automation with Claude Haiku 3.5 for Open API Specification

This project automates the generation of Cucumber test cases based on Open API specifications, utilizing Claude Haiku 3.5, an AI model by Anthropic. The focus of the project is on using prompts to automatically generate test cases for REST APIs defined in the Open API specification, and the architecture integrates Lambda, S3, and email notifications for seamless operation.

Key Components:

1. Cucumber Test Case Generation:
- Prompt-Driven: The project uses Claude Haiku 3.5 to generate detailed test cases for REST APIs based on the provided Open API specification.
- Automated Test Case Writing: Using the prompt to describe the API functionality, the AI model generates comprehensive test cases that ensure API endpoints perform as expected.

2. Architecture Overview:
- Lambda Function: Processes the input Open API spec and invokes Claude Haiku 3.5 to generate the test cases. This Lambda function acts as a bridge to connect the AI model with the testing framework.
- S3 Integration: Once the test cases are generated, the Lambda function uploads the resulting files to a designated S3 bucket for storage and access.
- Email Notification: After the successful upload to S3, the Lambda function triggers an email notification, informing stakeholders about the successful generation and storage of the test cases.

Steps Involved:
1. Open API Spec: The input Open API specification is provided to the system.
2. Prompt to Claude Haiku 3.5: A prompt is sent to the Claude Haiku 3.5 model to generate appropriate test cases based on the provided spec.
3. Test Case Generation: Claude Haiku 3.5 processes the input and generates corresponding test cases.
4. Lambda Execution: The Lambda function handles the orchestration, invoking the AI model, managing the output, and uploading it to S3.
5. S3 Upload: The test case files are stored in an S3 bucket for easy access.
6. Email Notification: After successful storage, an email is sent confirming the upload of the test cases to S3.