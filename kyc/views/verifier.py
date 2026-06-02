from django.shortcuts import render, redirect


def verifier_dashboard(request):
    return render(request, "kyc/verifier/verifier_dashboard.html")

def verifier_review_queue(request):
    return render(request, "kyc/verifier/review_queue.html")

def verifier_document_review(request):
    return render(request, "kyc/verifier/document_review.html")

def verifier_verification_history(request):
    return render(request, "kyc/verifier/verification_history.html")
