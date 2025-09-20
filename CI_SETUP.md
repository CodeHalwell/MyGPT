# CI/CD Setup Instructions

## GitHub Actions Secrets Configuration

The GitHub Actions CI workflow requires certain secrets to be configured in your repository settings for secure operation. This guide explains how to set up these secrets.

### Required Secrets

The following secrets must be configured in your GitHub repository:

1. **`POSTGRES_PASSWORD`** - Password for the PostgreSQL database used in testing
2. **`FLASK_SECRET_KEY`** - Secret key for Flask application security

### How to Add Secrets to Your Repository

1. **Navigate to Repository Settings**
   - Go to your GitHub repository
   - Click on the **Settings** tab
   - In the left sidebar, expand **Secrets and variables**
   - Click on **Actions**

2. **Add Each Secret**
   - Click the **New repository secret** button
   - Enter the secret name and value as specified below
   - Click **Add secret**

### Secret Configuration Details

#### POSTGRES_PASSWORD
- **Name**: `POSTGRES_PASSWORD`
- **Value**: Choose a secure password for PostgreSQL (e.g., `your_secure_postgres_password`)
- **Usage**: Used for both the PostgreSQL service and database connection string in CI

#### FLASK_SECRET_KEY
- **Name**: `FLASK_SECRET_KEY`
- **Value**: A randomly generated secret key for Flask security (e.g., `your_flask_secret_key_here`)
- **Usage**: Used for Flask session security and CSRF protection
- **Generation**: You can generate a secure key using:
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```

### Example Secret Values

**Important**: Use your own secure values, not these examples!

```
POSTGRES_PASSWORD: MySecureDBPassword123!
FLASK_SECRET_KEY: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```

### Verification

After adding the secrets:

1. The repository secrets page should show both secrets listed (values will be hidden)
2. GitHub Actions workflows will have access to these secrets via `${{ secrets.SECRET_NAME }}`
3. The CI workflow will run without exposing sensitive information in logs

### Security Best Practices

- **Never commit secrets to your repository**
- **Use strong, randomly generated passwords**
- **Regularly rotate secrets for enhanced security**
- **Limit access to repository settings to trusted team members**
- **Review and audit secret usage periodically**

### Troubleshooting

If your CI workflow fails with authentication errors:

1. **Verify Secret Names**: Ensure secret names exactly match what's used in the workflow
2. **Check Secret Values**: Verify there are no trailing spaces or special characters
3. **Review Logs**: Check GitHub Actions logs for specific error messages (secrets values won't be shown)

For more information about GitHub Actions secrets, see: [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)