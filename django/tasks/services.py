from django import forms
from service_objects.services import Service
from service_objects.fields import DictField
from .models import Task


class QueueTask(Service):
    task_type = forms.CharField()
    payload = DictField()

    def process(self):
        task_type = self.cleaned_data["task_type"]
        payload = self.cleaned_data["payload"]

        task = Task.objects.create(task_type=task_type, payload=payload)
