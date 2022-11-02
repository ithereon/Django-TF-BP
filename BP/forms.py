from django import forms
from .models import Doc_Template

class Doc_Template_Update_Form(forms.ModelForm):
    class Meta:
        model = Doc_Template
        # fields = '__all__'
        fields = ['x_coord', 'y_coord', 'font', 'font_size', 'line_spacing', 'target_page']

    def __init__(self, *args, **kwargs):
        super(Doc_Template_Update_Form, self).__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-sm'})
    