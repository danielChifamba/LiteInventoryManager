from django import forms
from .models import *

# ############################################################## #
                    # Product Create Form #
# ############################################################## #
class ProductCreateForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name','category','description','cost_price','selling_price','stock_quantity', 'min_stock_level'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','id':'name'}),
            'category': forms.Select(attrs={'class':'form-control','id':'category'}),
            'description': forms.Textarea(attrs={'class':'form-control','id':'description','rows': 2,'cols': 20}),
            'cost_price': forms.NumberInput(attrs={'class':'form-control','id':'cost','min': 0.0,'onchange': 'changeBorderColor(this)'}),
            'selling_price': forms.NumberInput(attrs={'class':'form-control','id':'sell','min': 0.}),
            'stock_quantity': forms.NumberInput(attrs={'class':'form-control','id':'quantity','min': 0}),
            'min_stock_level': forms.NumberInput(attrs={'class':'form-control', 'id':'minStockLevel'}),
        }
# ############################################################## #
                    # Product Edit Form #
# ############################################################## #
class ProductEditForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name','category','description','cost_price','selling_price','stock_quantity','min_stock_level'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control input-safe','id':'nameEdit','onchange': 'changeBorderColor(this)'}),
            'category': forms.Select(attrs={'class':'form-control input-safe','id':'categoryEdit','onchange': 'changeBorderColor(this)'}),
            'description': forms.Textarea(attrs={'class':'form-control input-safe','id':'descriptionEdit','rows': 2,'cols': 20,'onchange': 'changeBorderColor(this)'}),
            'cost_price': forms.NumberInput(attrs={'class':'form-control input-safe','id':'costEdit','min': 0.0,'onchange': 'changeBorderColor(this)'}),
            'selling_price': forms.NumberInput(attrs={'class':'form-control input-safe','id':'sellEdit','min': 0.0,'onchange': 'changeBorderColor(this)'}),
            'stock_quantity': forms.NumberInput(attrs={'class':'form-control input-safe','id':'quantityEdit','min': 0,'onchange': 'changeBorderColor(this)'}),
            'min_stock_level': forms.NumberInput(attrs={'class':'form-control input-safe', 'id':'minStockLevelEdit','min': 0,'onchange': 'changeBorderColor(this)'}),
        }

# ############################################################## #
                    # Category Create Form #
# ############################################################## #
class CategoryCreateForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = [
            'name','description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control','id':'name'}),
            'description': forms.Textarea(attrs={'class':'form-control','id':'description','rows': 2,'cols': 20,}),
        }
        
# ############################################################## #
                    # Category Edit Form #
# ############################################################## #
class CategoryEditForm(forms.ModelForm):
    
    class Meta:
        model = Category
        fields = [
            'name','description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control input-safe','id':'nameEdit','onchange': 'changeBorderColor(this)'}),
            'description': forms.Textarea(attrs={'class':'form-control input-safe','id':'descriptionEdit','rows': 2,'cols': 20,'onchange': 'changeBorderColor(this)'}),
        }

# ############################################################## #
                    # Cashier Create Form #
# ############################################################## #
class CashierCreateForm(forms.Form):
    USERNAME_ATTR = {
        'class':'form-control',
        'id':'username',
        'required': True,
    }

    FIRST_NAME_ATTR = {
        'class':'form-control',
        'id':'first_name',
        'required': True,
    }

    LAST_NAME_ATTR = {
        'class':'form-control',
        'id':'last_name',
        'required': True,
    }

    EMAIL_ATTR = {
        'class':'form-control',
        'id':'email',
        'required': True,
    }

    PHONE_NUMBER_ATTR = {
        'class':'form-control',
        'id':'number',
        'required': True,
        'type': 'tel',
    }

    PASSWORD_ATTR = {
        'class':'form-control',
        'id': 'password',
        'required': True,
    }

    CONFIRM_PASSWORD_ATTR = {
        'class':'form-control',
        'id': 'confirm_password',
        'required': True,
    }

    username = forms.CharField(widget=forms.TextInput(attrs=USERNAME_ATTR))
    first_name = forms.CharField(widget=forms.TextInput(attrs=FIRST_NAME_ATTR))
    last_name = forms.CharField(widget=forms.TextInput(attrs=LAST_NAME_ATTR))
    email = forms.EmailField(widget=forms.TextInput(attrs=EMAIL_ATTR))
    phone_number = forms.CharField(widget=forms.TextInput(attrs=PHONE_NUMBER_ATTR))
    password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs=PASSWORD_ATTR))
    confirm_password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs=CONFIRM_PASSWORD_ATTR))
# ############################################################## #
                    # Cashier Edit Form #
# ############################################################## #
class CashierEditForm(forms.Form):
    USERNAME_ATTR = {
        'class':'form-control input-safe',
        'id':'usernameEdit',
        'required': True,
        'onchange': 'changeBorderColor(this)',
    }

    FIRST_NAME_ATTR = {
        'class':'form-control input-safe',
        'id':'first_nameEdit',
        'required': True,
        'onchange': 'changeBorderColor(this)',
    }

    LAST_NAME_ATTR = {
        'class':'form-control input-safe',
        'id':'last_nameEdit',
        'required': True,
        'onchange': 'changeBorderColor(this)',
    }

    EMAIL_ATTR = {
        'class':'form-control input-safe',
        'id':'emailEdit',
        'required': True,
        'onchange': 'changeBorderColor(this)',
    }

    PHONE_NUMBER_ATTR = {
        'class':'form-control input-safe',
        'id':'numberEdit',
        'required': True,
        'type': 'tel',
        'onchange': 'changeBorderColor(this)',
    }

    username = forms.CharField(widget=forms.TextInput(attrs=USERNAME_ATTR))
    first_name = forms.CharField(widget=forms.TextInput(attrs=FIRST_NAME_ATTR))
    last_name = forms.CharField(widget=forms.TextInput(attrs=LAST_NAME_ATTR))
    email = forms.EmailField(widget=forms.TextInput(attrs=EMAIL_ATTR))
    phone_number = forms.CharField(widget=forms.TextInput(attrs=PHONE_NUMBER_ATTR))
# ############################################################## #

class CreateExpensesForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'category', 'description', 'amount', 'receipt_image'
        ]
        widgets = {
            'category': forms.Select(attrs={'class':'form-control','id':'exp-category'}),
            'description': forms.Textarea(attrs={'class':'form-control','id':'exp-description','rows': 2,'cols': 20,'placeholder':'Enter description'}),
            'amount': forms.NumberInput(attrs={'class':'form-control','id':'exp-amount','min': 0}),
            'receipt_image': forms.FileInput(attrs={'class':'form-control','id':'exp-receipt'}),
        }

class UpdateExpensesForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = [
            'category', 'description', 'amount', 'receipt_image'
        ]
        widgets = {
            'category': forms.Select(attrs={'class':'form-control input-safe','id':'exp-category','onchange': 'changeBorderColor(this)'}),
            'description': forms.Textarea(attrs={'class':'form-control input-safe','id':'exp-description','rows': 2,'cols': 20,'placeholder':'Enter description','onchange': 'changeBorderColor(this)'}),
            'amount': forms.NumberInput(attrs={'class':'form-control input-safe','id':'exp-amount','min': 0,'onchange': 'changeBorderColor(this)'}),
            'receipt_image': forms.FileInput(attrs={'class':'form-control input-safe','id':'exp-receipt','onchange': 'changeBorderColor(this)'}),
        }

