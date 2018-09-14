import json

from django.http import QueryDict, HttpResponse

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, DetailView

from Post.models import Post
from Reply.forms import CreateForm, UpdateForm
from Reply.models import Reply


class ReplyCV(CreateView, DetailView):
    # model = Post
    form_class = CreateForm
    template_name = "reply/reply_create_form.html"

    def get_object(self, queryset=None):
        pk = self.kwargs['pk2']
        return Post.objects.get(id=pk)

    def form_valid(self, form):
        # form.instance.channel_id = self.kwargs['pk']
        form.instance.execute_time = form.instance.start_time
        form.instance.post_id = self.kwargs['pk2']
        return super(ReplyCV, self).form_valid(form)

    def get_success_url(self):
        channel_id = self.kwargs['pk']
        return reverse_lazy('Channel:Post:index', kwargs={'pk': channel_id})


class ReplyUV(UpdateView):
    form_class = UpdateForm
    template_name = "reply/reply_update_form.html"

    def get_object(self, queryset=None):
        pk = self.kwargs['pk2']
        return Post.objects.get(id=pk).reply

    def form_valid(self, form):
        form.instance.execute_time = form.instance.start_time
        return super(ReplyUV, self).form_valid(form)

    def get_success_url(self):
        channel_id = self.kwargs['pk']
        return reverse_lazy('Channel:Post:index', kwargs={'pk': channel_id})


class ReplyDV(DeleteView):
    model = Reply

    def get_object(self, queryset=None):
        pk = self.kwargs['pk2']
        return Post.objects.get(id=pk).reply

    def get_success_url(self):
        channel_id = self.kwargs['pk']
        return reverse_lazy('Channel:Post:index', kwargs={'pk': channel_id})


def trigger(request, pk, pk2):
    if request.method == "PUT":
        result = {
            "status": True
        }
        try:
            query_dict = QueryDict(request.body)
            status = query_dict.get('status')
            post = Post.objects.get(id=pk2)
            reply = post.reply
            if status == "on":
                reply.trigger = "1"
                reply.save()
                result["text"] = "off"
            else:
                reply.trigger = "0"
                reply.save()
                result["text"] = "on"
        except Exception as e:
            print(e)
            result["status"] = False
        return HttpResponse(json.dumps(result), content_type="application/json")
