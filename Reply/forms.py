from django import forms

from Reply.models import Reply


class CreateForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['start_time', 'end_time', 'interval_time', 'content']
        labels = {
            "start_time": "시작 시간",
            "end_time": "끝 시간",
            "interval_time": "작업 간격",
            "content": "댓글 내용",
        }
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'id': 'start_time', 'class': 'form-control datetimepicker', 'placeholder': '2018-09-10 12:00:00'}),
            'end_time': forms.DateTimeInput(
                attrs={'id': 'end_time', 'class': 'form-control datetimepicker', 'placeholder': '2018-09-17 12:00:00'}),
            'interval_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10'}),
            'content': forms.Textarea(attrs={'cols': 80, 'rows': 20, 'class': 'form-control'})
        }


class UpdateForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['start_time', 'end_time', 'interval_time', 'content']
        labels = {
            "start_time": "시작 시간",
            "end_time": "끝 시간",
            "interval_time": "작업 간격",
            "content": "댓글 내용",
        }
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': '2018-09-10 12:00:00'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'placeholder': '2018-09-17 12:00:00'}),
            'interval_time': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '10'}),
            'content': forms.Textarea(attrs={'cols': 80, 'rows': 20, 'class': 'form-control'})
        }
