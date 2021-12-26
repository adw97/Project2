from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Auction_Listing(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="list_creater")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=100)
    starting_bid = models.IntegerField()
    updated_bid = models.IntegerField()
    image = models.CharField(max_length=300)
    category = models.CharField(max_length=100)
    closed = models.BooleanField()
    
    def __str__(self):
        return f"{self.title}"

class Biddings(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidder")
    item = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE, related_name="item_name")
    bids = models.IntegerField()

    def __str__(self):
        return f"{self.bids}"

class Comments(models.Model):
    comment = models.TextField()
    commentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_comment")
    item_name = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE, related_name="item_title")

    def __str__(self):
        return f"{self.comment}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlister")
    listing = models.ForeignKey(Auction_Listing, on_delete=models.CASCADE, related_name="listed_item")
    is_watchlisted = models.BooleanField()

    def __str__(self):
        return f"{self.user} {self.listing}"