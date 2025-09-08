# questions/forms.py

from django import forms
from .models import QuestionUpload, QuestionPaper
from reference.models import Trade
from .services import is_encrypted_dat, decrypt_dat_content, load_questions_from_excel_data

class QuestionUploadForm(forms.ModelForm):
    decryption_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter decryption password',
            'class': 'form-control'
        }),
        help_text="Password required for encrypted DAT files"
    )
    
    trade = forms.ModelChoiceField(
        queryset=Trade.objects.order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Note: Do not select trade if paper is 'Secondary'",
        empty_label="-- Select Trade (Optional) --"
    )

    class Meta:
        model = QuestionUpload
        fields = ["file", "decryption_password", "trade"]
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        password = cleaned_data.get("decryption_password")

        if file and password:
            try:
                # Read file content into memory
                file.seek(0)
                file_content = file.read()
                file.seek(0)  # Reset file pointer

                # Basic validation - check if it looks like encrypted data
                if not is_encrypted_dat(file_content):
                    raise forms.ValidationError(
                        "File does not appear to be encrypted. Expected encrypted DAT file."
                    )

                # Test decryption with provided password
                try:
                    decrypted_data = decrypt_dat_content(file_content, password)
                    
                    # Verify it's a valid Excel file by checking magic bytes
                    if not decrypted_data.startswith(b'PK'):
                        raise forms.ValidationError(
                            "Decrypted data is not a valid Excel file format."
                        )
                    
                    # Try to parse the Excel data to validate structure
                    try:
                        questions = load_questions_from_excel_data(decrypted_data)
                        if not questions:
                            raise forms.ValidationError(
                                "No valid questions found in the Excel file."
                            )
                        
                        # Store for later use in signals
                        cleaned_data['validated_questions_count'] = len(questions)
                        
                    except Exception as e:
                        raise forms.ValidationError(
                            f"Error parsing Excel structure: {str(e)}"
                        )
                    
                except ValueError as e:
                    raise forms.ValidationError(
                        f"Decryption failed: {str(e)}. Please check your password."
                    )
                
                # Store file content for later use
                cleaned_data['file_content'] = file_content
                
            except forms.ValidationError:
                raise  # Re-raise form validation errors
            except Exception as e:
                raise forms.ValidationError(
                    f"Error processing file: {str(e)}"
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set the password from form data
        if 'decryption_password' in self.cleaned_data:
            instance.decryption_password = self.cleaned_data['decryption_password']
        
        # Set the trade from form data
        instance.trade = self.cleaned_data.get('trade')
        
        if commit:
            instance.save()
        
        return instance


# ---------------------------------------------------------
# Admin ModelForm: QuestionPaperAdminForm
# This form attaches inline JS (via widget attrs) so the admin
# will disable the `trade` field when question_paper == 'Secondary'
# and enforces the rule server-side as well.
# ---------------------------------------------------------
class QuestionPaperAdminForm(forms.ModelForm):
    class Meta:
        model = QuestionPaper
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Determine the field names in this form (robust to naming)
        qp_field_name = None
        trade_field_name = None
        for fname in self.fields:
            if fname == 'question_paper' or fname.lower().endswith('question_paper'):
                qp_field_name = fname
            if fname == 'trade' or fname.lower().endswith('trade'):
                trade_field_name = fname

        # If expected fields are missing, skip adding JS (safe fallback).
        if not qp_field_name or not trade_field_name:
            return

        # Build inline onchange JS that toggles the trade field.
        # It will:
        #  - disable trade and clear its value when qp == Secondary
        #  - enable trade otherwise
        trade_dom_id = 'id_%s' % trade_field_name
        # Note: Use triple-quoted string to keep readability
        onchange_js = (
            "(function(el){"
            "  var trade = document.getElementById('%s');"
            "  if(!trade){ trade = document.querySelector('[name=\"%s\"]'); }"
            "  var v = el.value || (el.options && el.options[el.selectedIndex] && el.options[el.selectedIndex].value);"
            "  var isSecondary = (String(v) === 'Secondary' || String(v).toLowerCase() === 'secondary');"
            "  if(isSecondary){"
            "    if(trade){ trade.disabled = true; try{ trade.value = ''; trade.dispatchEvent(new Event('change')); }catch(e){} }"
            "  } else {"
            "    if(trade){ trade.disabled = false; try{ trade.dispatchEvent(new Event('change')); }catch(e){} }"
            "  }"
            "})(this);"
        ) % (trade_dom_id, trade_field_name)

        # Append to any existing onchange attr on the question_paper widget
        existing = self.fields[qp_field_name].widget.attrs.get('onchange', '')
        if existing:
            self.fields[qp_field_name].widget.attrs['onchange'] = existing + ';' + onchange_js
        else:
            self.fields[qp_field_name].widget.attrs['onchange'] = onchange_js

        # If instance or initial indicates Secondary, mark trade widget disabled initially
        val = None
        try:
            if self.instance and getattr(self.instance, qp_field_name, None) is not None:
                val = getattr(self.instance, qp_field_name)
        except Exception:
            val = None

        if val is None:
            # check initial data or bound data
            if qp_field_name in self.initial:
                val = self.initial.get(qp_field_name)
            elif self.data and qp_field_name in self.data:
                val = self.data.get(qp_field_name)

        if val is not None and (str(val) == 'Secondary' or str(val).lower() == 'secondary'):
            # Mark the trade widget disabled for initial render
            self.fields[trade_field_name].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned = super().clean()

        # find the same field names
        qp_field_name = None
        trade_field_name = None
        for fname in self.fields:
            if fname == 'question_paper' or fname.lower().endswith('question_paper'):
                qp_field_name = fname
            if fname == 'trade' or fname.lower().endswith('trade'):
                trade_field_name = fname

        if qp_field_name and trade_field_name:
            qpv = cleaned.get(qp_field_name)
            if qpv is not None and (str(qpv) == 'Secondary' or str(qpv).lower() == 'secondary'):
                # enforce server-side: clear trade so clients can't bypass rule
                cleaned[trade_field_name] = None

        return cleaned