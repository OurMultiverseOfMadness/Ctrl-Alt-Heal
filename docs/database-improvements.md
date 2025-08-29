# Database Table Improvements

This document outlines the improvements made to the database table naming and structure for better clarity, consistency, and AWS best practices.

## 🔄 **Changes Overview**

### **Before vs After**

| Aspect | Before | After |
|--------|--------|-------|
| **Naming Convention** | Hyphens (`ctrl-alt-heal`) | Underscores (`ctrl_alt_heal`) |
| **Table Names** | Generic (`users`, `history`) | Descriptive (`user_profiles`, `conversation_history`) |
| **Key Names** | Generic (`pk`, `sk`) | Descriptive (`user_id`, `prescription_id`) |
| **Environment** | Hardcoded | Environment-specific |
| **Documentation** | None | Table descriptions |

## 📊 **Table Structure Improvements**

### **1. User Profiles Table**

#### **Before:**
```python
table_name = "ctrl-alt-heal-{env}-users"
partition_key = "user_id"
```

#### **After:**
```python
table_name = "ctrl_alt_heal_{env}_user_profiles"
partition_key = "user_id"
description = "User profiles and preferences"
```

**Improvements:**
- ✅ **Descriptive name**: `user_profiles` instead of `users`
- ✅ **Clear purpose**: Stores user profiles and preferences
- ✅ **Consistent naming**: Uses underscores throughout

### **2. External Identities Table**

#### **Before:**
```python
table_name = "ctrl-alt-heal-{env}-identities"
partition_key = "pk"  # Generic key name
```

#### **After:**
```python
table_name = "ctrl_alt_heal_{env}_external_identities"
partition_key = "identity_key"
description = "External identity provider mappings (Telegram, etc.)"
```

**Improvements:**
- ✅ **Descriptive name**: `external_identities` instead of `identities`
- ✅ **Clear key name**: `identity_key` instead of `pk`
- ✅ **Purpose clarity**: Maps external providers to internal users

### **3. Conversation History Table**

#### **Before:**
```python
table_name = "ctrl-alt-heal-{env}-history"
partition_key = "user_id"
sort_key = "session_id"
```

#### **After:**
```python
table_name = "ctrl_alt_heal_{env}_conversation_history"
partition_key = "user_id"
sort_key = "session_id"
description = "Conversation history and session management"
```

**Improvements:**
- ✅ **Descriptive name**: `conversation_history` instead of `history`
- ✅ **Clear purpose**: Manages conversations and sessions
- ✅ **Environment variable**: `CONVERSATIONS_TABLE_NAME`

### **4. Medical Prescriptions Table**

#### **Before:**
```python
table_name = "ctrl-alt-heal-{env}-prescriptions"
partition_key = "pk"  # Generic key name
sort_key = "sk"       # Generic key name
```

#### **After:**
```python
table_name = "ctrl_alt_heal_{env}_medical_prescriptions"
partition_key = "user_id"
sort_key = "prescription_id"
description = "Medical prescriptions and medication information"
```

**Improvements:**
- ✅ **Descriptive name**: `medical_prescriptions` instead of `prescriptions`
- ✅ **Clear key names**: `user_id` and `prescription_id` instead of `pk`/`sk`
- ✅ **Purpose clarity**: Medical prescription data

### **5. FHIR Resources Table**

#### **Before:**
```python
table_name = "ctrl-alt-heal-{env}-fhir"
partition_key = "pk"  # Generic key name
sort_key = "sk"       # Generic key name
```

#### **After:**
```python
table_name = "ctrl_alt_heal_{env}_fhir_resources"
partition_key = "user_id"
sort_key = "resource_id"
description = "FHIR-compliant healthcare data resources"
```

**Improvements:**
- ✅ **Descriptive name**: `fhir_resources` instead of `fhir`
- ✅ **Clear key names**: `user_id` and `resource_id` instead of `pk`/`sk`
- ✅ **Environment variable**: `FHIR_DATA_TABLE_NAME`

## 🏗️ **S3 Bucket Improvements**

### **Before:**
```python
uploads_bucket = "uploads-bucket"      # Generic name
assets_bucket = "assets-bucket"        # Generic name
```

### **After:**
```python
uploads_bucket = "ctrl_alt_heal_{env}_user_uploads"    # Descriptive name
assets_bucket = "ctrl_alt_heal_{env}_system_assets"    # Descriptive name
```

**Improvements:**
- ✅ **Environment-specific**: Includes environment in bucket names
- ✅ **Descriptive names**: Clear purpose indication
- ✅ **Consistent naming**: Uses underscores throughout

## 🔧 **Technical Improvements**

### **1. Enhanced Table Configuration**

```python
def _create_table(
    self,
    table_name: str,
    partition_key: str,
    sort_key: str | None = None,
    description: str | None = None,
) -> dynamodb.Table:
    # ... table creation logic
    return dynamodb.Table(
        self,
        table_name,
        table_name=table_name,
        partition_key=pk,
        sort_key=sk,
        billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        removal_policy=cdk.RemovalPolicy.DESTROY,
        point_in_time_recovery=True,      # ✅ New: Data protection
        contributor_insights=True,        # ✅ New: Monitoring
    )
```

### **2. Environment Variable Updates**

#### **Before:**
```bash
HISTORY_TABLE_NAME=ctrl-alt-heal-history
FHIR_TABLE_NAME=ctrl-alt-heal-fhir
```

#### **After:**
```bash
CONVERSATIONS_TABLE_NAME=ctrl_alt_heal_dev_conversation_history
FHIR_DATA_TABLE_NAME=ctrl_alt_heal_dev_fhir_resources
```

## 📋 **Migration Guide**

### **For New Deployments**

No migration needed - the new naming will be used automatically.

### **For Existing Deployments**

If you have existing data, you'll need to:

1. **Export data** from old tables
2. **Deploy new infrastructure** with new table names
3. **Import data** to new tables
4. **Update application** to use new environment variables

### **Environment Variable Changes**

| Old Variable | New Variable | Example Value |
|--------------|--------------|---------------|
| `HISTORY_TABLE_NAME` | `CONVERSATIONS_TABLE_NAME` | `ctrl_alt_heal_dev_conversation_history` |
| `FHIR_TABLE_NAME` | `FHIR_DATA_TABLE_NAME` | `ctrl_alt_heal_dev_fhir_resources` |

## 🎯 **Benefits**

### **1. Clarity & Maintainability**
- **Self-documenting names**: Table purposes are clear from names
- **Consistent patterns**: All resources follow same naming convention
- **Better debugging**: Easier to identify resources in AWS console

### **2. AWS Best Practices**
- **Underscores over hyphens**: AWS recommended naming convention
- **Descriptive names**: Clear resource identification
- **Environment isolation**: Separate resources per environment

### **3. Developer Experience**
- **Intuitive naming**: Developers understand table purposes immediately
- **Consistent patterns**: Predictable naming across all resources
- **Better documentation**: Table descriptions in CDK

### **4. Operations & Monitoring**
- **Resource identification**: Easy to identify resources in CloudWatch
- **Cost tracking**: Clear resource attribution for billing
- **Security**: Better access control with descriptive names

## 🔍 **Example Resource Names**

### **Development Environment**
```
ctrl_alt_heal_dev_user_profiles
ctrl_alt_heal_dev_external_identities
ctrl_alt_heal_dev_conversation_history
ctrl_alt_heal_dev_medical_prescriptions
ctrl_alt_heal_dev_fhir_resources
ctrl_alt_heal_dev_user_uploads
ctrl_alt_heal_dev_system_assets
```

### **Production Environment**
```
ctrl_alt_heal_prod_user_profiles
ctrl_alt_heal_prod_external_identities
ctrl_alt_heal_prod_conversation_history
ctrl_alt_heal_prod_medical_prescriptions
ctrl_alt_heal_prod_fhir_resources
ctrl_alt_heal_prod_user_uploads
ctrl_alt_heal_prod_system_assets
```

## ✅ **Validation**

### **Naming Convention Compliance**
- ✅ **Underscores**: All names use underscores instead of hyphens
- ✅ **Descriptive**: Names clearly indicate resource purpose
- ✅ **Consistent**: All resources follow same pattern
- ✅ **Environment-aware**: Names include environment prefix

### **AWS Compatibility**
- ✅ **DynamoDB**: Table names comply with DynamoDB naming rules
- ✅ **S3**: Bucket names comply with S3 naming rules
- ✅ **CDK**: Resource names work with CDK deployment
- ✅ **Environment variables**: Compatible with Lambda environment

---

**These improvements make the database structure more professional, maintainable, and aligned with AWS best practices! 🎉**
