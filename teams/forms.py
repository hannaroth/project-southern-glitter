from django import forms

from .models import DIET_CHOICES, Team


class TeamSignupForm(forms.ModelForm):
    dietary_restrictions = forms.MultipleChoiceField(
        choices=DIET_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Dietary restrictions",
    )

    class Meta:
        model = Team
        fields = ("address", "dietary_restrictions", "dietary_notes", "preferred_course")
        labels = {
            "address": "Our address (where we host our course)",
            "dietary_notes": "Other dietary needs",
            "preferred_course": "Course we'd like to host",
        }
        widgets = {"preferred_course": forms.RadioSelect}

    def clean_address(self):
        address = self.cleaned_data["address"].strip()
        if not address:
            raise forms.ValidationError("Please enter your address.")
        return address
