# Review App Test

This file is created to test the review app functionality.

## What this tests:
- Automatic review app creation on pull requests
- Review app deployment with proper environment variables
- Automatic cleanup when PR is closed

## Expected behavior:
1. When this PR is created, a review app should be automatically deployed
2. The review app URL should be posted as a comment on the PR
3. When the PR is closed, the review app should be automatically deleted 