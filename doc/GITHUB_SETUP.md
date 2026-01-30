# GitHub Repository Setup

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `deal-validator`
3. Description: `Salesforce loan validation system with Azure Functions`
4. **Private** repository (recommended for proprietary code)
5. **Do NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

## Step 2: Configure Azure Credentials

### Get Azure Service Principal Credentials

Run this command in Azure CLI:

```bash
az ad sp create-for-rbac \
  --name "deal-validator-github-actions" \
  --role contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>/resourceGroups/LPC_amortengine_dev \
  --sdk-auth
```

This will output JSON like:
```json
{
  "clientId": "xxxx",
  "clientSecret": "xxxx",
  "subscriptionId": "xxxx",
  "tenantId": "xxxx",
  ...
}
```

**Copy the entire JSON output** - you'll need it in the next step.

### Add Secret to GitHub

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `AZURE_CREDENTIALS`
5. Value: **Paste the entire JSON output from above**
6. Click **"Add secret"**

## Step 3: Push Code to GitHub

From your local repository:

```bash
# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/deal-validator.git

# Create and switch to main branch
git branch -M main

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Deal validator with Azure Functions"

# Push to GitHub
git push -u origin main

# Create and push dev branch
git checkout -b dev
git push -u origin dev
```

## Step 4: Verify GitHub Actions

1. Go to your GitHub repository
2. Navigate to the **"Actions"** tab
3. You should see the workflow ready to run
4. Push any change to the `dev` branch to trigger deployment:

```bash
# Make a small change
echo "# Test" >> doc/README.md

# Commit and push
git add doc/README.md
git commit -m "Test deployment"
git push origin dev
```

5. Watch the deployment in the Actions tab

## Step 5: Configure Azure Function App

Ensure your Azure Function App `deal-validator-v1` exists and has:

### Application Settings

Add these in Azure Portal → Function App → Configuration:

```
SF_CLIENT_ID=<your_salesforce_client_id>
SF_CLIENT_SECRET=<your_salesforce_client_secret>
SF_CLIENT_URL=<your_salesforce_oauth_url>
```

### Runtime Settings

- **Runtime stack**: Python
- **Version**: 3.11
- **Operating System**: Linux

## Step 6: Test Deployment

After successful deployment:

```bash
# Test health endpoint
curl https://deal-validator-v1.azurewebsites.net/api/health

# Test validation endpoint (with function key)
curl "https://deal-validator-v1.azurewebsites.net/api/validate/id/a0iVy00000ETkIkIAL?code=YOUR_FUNCTION_KEY"
```

## Workflow Triggers

The deployment workflow triggers when:
- ✅ Push to `dev` branch
- ✅ Changes to `core/**`
- ✅ Changes to `functionapp.py`
- ✅ Changes to `requirements.txt`
- ✅ Changes to `host.json`
- ✅ Changes to `.github/workflows/deploy-to-azure-dev.yml`

Changes to these do **NOT** trigger deployment:
- ❌ `doc/**` (documentation)
- ❌ `regression_tests/**` (tests)
- ❌ `archive/**` (old files)
- ❌ `*.md` files (documentation)

## Troubleshooting

### Deployment Fails

1. **Check Azure credentials**: Ensure `AZURE_CREDENTIALS` secret is set correctly
2. **Check Function App name**: Verify `deal-validator-v1` exists in Azure
3. **Check Resource Group**: Verify `LPC_amortengine_dev` exists and you have access
4. **Check logs**: Go to Actions tab → Click on failed workflow → View logs

### Function App Not Working

1. **Check Application Settings**: Ensure Salesforce credentials are set
2. **Check Runtime**: Verify Python 3.11 is selected
3. **Check Logs**: Azure Portal → Function App → Log stream

### Authentication Errors

If you get authentication errors:

```bash
# Verify Service Principal has access
az role assignment list --assignee <CLIENT_ID> --resource-group LPC_amortengine_dev
```

## Security Best Practices

1. **Never commit credentials**: Always use GitHub Secrets and Azure Application Settings
2. **Use Private Repository**: For proprietary code
3. **Limit Service Principal scope**: Only grant access to specific resource group
4. **Rotate credentials regularly**: Update Service Principal credentials periodically
5. **Review deployment logs**: Check for any exposed secrets or errors

## Branch Strategy

- **`main`** branch: Production-ready code (not auto-deployed)
- **`dev`** branch: Development code (auto-deploys to `deal-validator-v1`)

To create a production deployment workflow:
1. Copy `.github/workflows/deploy-to-azure-dev.yml`
2. Rename to `deploy-to-azure-prod.yml`
3. Update branch to `main`
4. Update function app name to production app
5. Use `AZURE_CREDENTIALS_PROD` secret

## Support

For issues:
1. Check GitHub Actions logs
2. Check Azure Function App logs
3. File an issue in the repository
4. Contact DevOps team
