from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ..models import SubCategory, MainCategory


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_categories_by_direction(request, direction):
    """
    API endpoint to get categories filtered by transaction direction.
    
    Args:
        request: The HTTP request
        direction: The transaction direction ('IN' for income, 'OUT' for outcome)
    
    Returns:
        JsonResponse: A JSON response containing the categories
    """
    # Map transaction direction to category type
    direction_to_category_type = {
        'IN': 'INC',  # Income
        'OUT': 'EXP',  # Expense
    }
    
    category_type = direction_to_category_type.get(direction)
    
    if not category_type:
        return JsonResponse({'error': 'Invalid direction'}, status=400)
    
    # Get main categories for the current user and the specified type
    main_categories = MainCategory.objects.filter(
        user_id=request.user.id,
        category_type=category_type
    )
    
    # Get all subcategories for these main categories
    subcategories = SubCategory.objects.filter(
        parent_category__in=main_categories
    ).select_related('parent_category')
    
    # Format the response
    categories = [
        {
            'id': subcategory.id,
            'name': subcategory.name,
            'main_category_id': subcategory.parent_category.id,
            'main_category_name': subcategory.parent_category.name,
        }
        for subcategory in subcategories
    ]
    
    return JsonResponse({'categories': categories}) 