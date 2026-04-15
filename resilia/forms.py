from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import AnxietyTrigger
from .models import JournalEntry



from django import forms
from .models import JournalEntry

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['trigger', 'title', 'content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['trigger'].widget.attrs.update({'class': 'form-control'})
        self.fields['title'].widget.attrs.update({'class': 'form-control'})
        self.fields['content'].widget.attrs.update({
            'class': 'form-control',
            'rows': 6
        })

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", 'first_name', 'last_name', "email", "password1", "password2"]


class AnxietyTriggerForm(forms.ModelForm):
    class Meta:
        model = AnxietyTrigger
        # CBT order + your extra bits
        fields = [
            "title",
            "situation",   # Trigger
            "thoughts",    # Thought
            "feelings",    # Emotion
            "intensity",   # Emotion intensity
            "behaviour",   # Behaviour
            "outcome",     # Outcome
            "date",
        ]

        labels = {
            "title": "Short title (optional)",
            "situation": "Trigger (what happened?)",
            "thoughts": "Thought (what went through your mind?)",
            "feelings": "Emotion (how did you feel in your body?)",
            "intensity": "Anxiety level (1–10)",
            "behaviour": "Behaviour (what did you do or avoid?)",
            "outcome": "Outcome (what was the result?)",
            "date": "Date of this trigger",
        }

        widgets = {
            "title": forms.TextInput(),
            "situation": forms.Textarea(attrs={"rows": 4}),
            "thoughts": forms.Textarea(attrs={"rows": 4}),
            "feelings": forms.Textarea(attrs={"rows": 4}),
            "intensity": forms.NumberInput(attrs={"min": 1, "max": 10}),
            "behaviour": forms.Textarea(attrs={"rows": 3}),
            "outcome": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ["trigger", "title", "content"]



class OrganisationContactForm(forms.Form):
    organisation_name = forms.CharField(label="Organisation Name", max_length=150)
    contact_name = forms.CharField(label="Your Name", max_length=100)
    email = forms.EmailField(label="Work Email")
    role = forms.CharField(label="Your Role", max_length=100, required=False)
    organisation_type = forms.CharField(label="Organisation Type", max_length=100, required=False)
    message = forms.CharField(widget=forms.Textarea, label="How can we support you?")
