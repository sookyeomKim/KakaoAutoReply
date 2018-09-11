from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView

from FileUpload.forms import FileFieldForm
from FileUpload.models import FileUpload


class FileUploadLV(FormView, ListView):
    model = FileUpload
    form_class = FileFieldForm
    success_url = reverse_lazy("FileUpload:index")
    def post(self, request, *args, **kwargs):
        form = FileFieldForm(request.POST, request.FILES)
        if form.is_valid():
            instance = FileUpload(file=request.FILES['file_field'])
            instance.save()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

