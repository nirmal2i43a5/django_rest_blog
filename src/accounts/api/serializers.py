from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

from django.db.models import Q

from rest_framework.serializers import (
    CharField,
    EmailField,
    
    HyperlinkedIdentityField,
    ModelSerializer,
    SerializerMethodField,
    ValidationError
    )


User = get_user_model()


class UserDetailSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
        ]




class UserCreateSerializer(ModelSerializer):
    email = EmailField(label='Email Address')
    email2 = EmailField(label='Confirm Email')
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'email2',
            'password',
            
        ]
        
        extra_kwargs = {"password":
                            {"write_only": True}
                            }#means when password is not seen in json format 
        
    # def validate(self, data):
   
    #     return data

    #there are two email so i need to validate that
    
    #for email first
    def validate_email(self, value):
        # value = actual value passed to email
        data = self.get_initial()#give the initial data that have been passed
        email1 = data.get("email2")
        email2 = value
        if email1 != email2:
            raise ValidationError("Emails must match.")
        
        
        user_qs = User.objects.filter(email=email2)
        if user_qs.exists():
            raise ValidationError("This user has already registered.")
        return value

    #for email2
    def validate_email2(self, value):
        data = self.get_initial()#to show validatoin error in email confirm i need email
        email1 = data.get("email")
        email2 = value
        if email1 != email2:
            raise ValidationError("Emails must match.")
        return value


    #overriding create builtin method
    def create(self, validated_data):#this logic is also akin to the normal register but we are using validate_data 
        username = validated_data['username']
        email = validated_data['email']
        password = validated_data['password']
        user_obj = User(
                username = username,
                email = email
            )
        user_obj.set_password(password)
        user_obj.save()
        return validated_data



class UserLoginSerializer(ModelSerializer):
    token = CharField(allow_blank=True, read_only=True)
    username = CharField()
    email = EmailField(label='Email Address')
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'token',
            
        ]
        extra_kwargs = {"password":
                            {"write_only": True}
                            }
        
    #validate for incorrect details
    def validate(self, data):#data is built in dict
        user_obj=None
        email = data.get('email',None)#if no email then None
        username = data.get('username',None)
        password = data.get('password')
        
        if not email and not username:
            raise ValidationError("A username and email is required to login")
        
        user = User.objects.filter(Q(email=email)|
                                   Q(username=username)).distinct()
        
        
        
        # user = user.exclude(email__isnull=True).exclude(email__iexact='')#it excludes null email and give relevant output
        print(user)
        if user.exists() and user.count() == 1:
            
            user_obj = user.first()#only one user obj so we set first
        else:
            raise ValidationError("The email/username is not valid")
            
        if user_obj:
            if not user_obj.check_password(password):
                raise ValidationError("Incorrect credentials please try again")
        #otherwise
        data['token'] = "random token"
        
            
        # email = data['email']
        # user_qs = User.objects.filter(email=email)
        # if user_qs.exists():
        #     raise ValidationError("This user has already registered.")
        return data
