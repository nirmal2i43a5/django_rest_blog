
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_save
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.text import slugify


from markdown_deux import markdown
from comments.models import Comment

from .utils import get_read_time

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField

from PIL import Image
class PostManager(models.Manager):
    
    def active(self, *args, **kwargs):
        
        # Post.objects.all() is similar to  super(PostManager, self).all()
        return super(PostManager, self).filter(draft=False).filter(publish__lte=timezone.now())



class Post(models.Model):
    #associate post with particular user i.e different staff in the office can create different post and it show username for the post they have created
    #AUTH_USER_MODEL is the default user model
    #default = 1 means for first user ie.admin ,superadmin,user
    user = models.ForeignKey(settings.AUTH_USER_MODEL, default=1)
    
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='Images', 
            null=True, 
            blank=True, 
            width_field="width_field", 
            height_field="height_field")
    height_field = models.IntegerField(default=0)
    width_field = models.IntegerField(default=0)
    
    content = RichTextUploadingField(null=True,blank=True)
    
    draft = models.BooleanField(default=False)#true means post is not ready to publish i.e admin and staff can only see this and publish it later
    publish = models.DateField(auto_now=False, auto_now_add=False)
    read_time =  models.IntegerField(default=0) # models.TimeField(null=True, blank=True) #assume minutes
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)

    objects = PostManager()


    def __str__(self):
        return self.title
    
    def save(self):
        super().save()

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def get_absolute_url(self):
        return reverse("posts:detail", kwargs={"slug": self.slug})

    def get_api_url(self):
        return reverse("posts-api:detail", kwargs={"slug": self.slug})
    class Meta:
        ordering = ["-timestamp", "-updated"]

    def get_markdown(self):
        content = self.content
        markdown_text = markdown(content)
        return mark_safe(markdown_text)


    @property
    def comments(self):
        instance = self
        qs = Comment.objects.filter_by_instance(instance)
        return qs

    @property
    def get_content_type(self):
        instance = self
        # print(instance,"-----------")
        content_type = ContentType.objects.get_for_model(instance.__class__)
        return content_type







def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Post.objects.filter(slug=slug).order_by("-id")
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" %(slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug


def pre_save_post_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug = create_slug(instance)

    if instance.content:
        html_string = instance.get_markdown()#I can also directly use instance.content without markdown but text is not safe as it might sometimes show with html tags 
        read_time_var = get_read_time(html_string)
        instance.read_time = read_time_var
                #(read_time) is the field here
        
        
pre_save.connect(pre_save_post_receiver, sender=Post)










