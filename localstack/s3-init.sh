#!/bin/bash
echo "LocalStack startup script: Creating S3 bucket..."

awslocal s3 mb s3://$S3_BUCKET_CONFIG

echo "✅ S3 bucket created."
