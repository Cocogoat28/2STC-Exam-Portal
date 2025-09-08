# from django.shortcuts import render
# from .models import QuestionPaper, PaperQuestion

# def exam_interface(request):
#     # Fetch the latest paper or by ID; adjust as needed
#     paper = QuestionPaper.objects.latest('id')  # Or get specific: .get(id=1)
    
#     # Get questions through the PaperQuestion relationship, properly ordered
#     paper_questions = PaperQuestion.objects.filter(
#         paper=paper
#     ).select_related('question').order_by('order', 'id')
    
#     # Extract the actual Question objects
#     questions = [pq.question for pq in paper_questions]
    
#     # Debug info
#     print(f"Paper: {paper.question_paper}")
#     print(f"Found {len(questions)} questions")
#     for i, q in enumerate(questions[:3]):  # Print first 3 for debugging
#         print(f"Q{i+1}: {q.part} - {q.text[:50]}...")

#     duration_seconds = int(paper.exam_duration.total_seconds()) if paper.exam_duration else 0

#     context = {
#         'part_a': paper,
#         'questions': questions,  # Add this line
#         'duration_seconds': duration_seconds,
#     }
#     return render(request, 'registration/exam_interface.html', context)


from django.shortcuts import render
from .models import QuestionPaper, PaperQuestion

def exam_interface(request):
    # Fetch the latest paper or by ID; adjust as needed
    paper = QuestionPaper.objects.latest('id')  # Or get specific: .get(id=1)
    
    # Get questions through the PaperQuestion relationship, properly ordered
    paper_questions = PaperQuestion.objects.filter(
        paper=paper
    ).select_related('question').order_by('order', 'id')
    
    # Extract the actual Question objects
    questions = [pq.question for pq in paper_questions]
    
    # Debug info
    print(f"Paper: {paper.title}")
    print(f"Found {len(questions)} questions")
    for i, q in enumerate(questions[:3]):  # Print first 3 for debugging
        print(f"Q{i+1}: {q.part} - {q.text[:50]}...")

    duration_seconds = int(paper.exam_duration.total_seconds()) if paper.exam_duration else 0

    context = {
        'part_a': paper,
        'questions': questions,  # Add this line
        'duration_seconds': duration_seconds,
    }
    return render(request, 'registration/exam_interface.html', context)