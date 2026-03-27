# import firebase_admin
# from firebase_admin import credentials, firestore


# # Initialize Firebase Admin
# cred = credentials.Certificate("../serviceAccountKey.json")  # Path to your service account
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# # Sample data
# sample_dishes = [
#     {
#         "name": "Spaghetti Carbonara",
#         "description": "Classic Italian pasta with eggs, cheese, pancetta, and black pepper.",
#         "cuisine": "Italian",
#         "image_url": "https://www.themealdb.com/images/media/meals/llcbn01574260722.jpg"
#     },
#     {
#         "name": "Chicken Tikka Masala",
#         "description": "Chunks of grilled chicken simmered in a creamy spiced tomato sauce.",
#         "cuisine": "Indian",
#         "image_url": "https://www.themealdb.com/images/media/meals/wyxwsp1486979827.jpg"
#     },
#     {
#         "name": "Sushi Platter",
#         "description": "Assorted sushi rolls with fresh fish, vegetables, and rice.",
#         "cuisine": "Japanese",
#         "image_url": "https://www.themealdb.com/images/media/meals/g046bb1663960946.jpg"
#     },
#     {
#         "name": "Beef Tacos",
#         "description": "Crispy taco shells filled with seasoned beef, lettuce, and cheese.",
#         "cuisine": "Mexican",
#         "image_url": "https://www.themealdb.com/images/media/meals/qtuwxu1468233098.jpg"
#     },
#     {
#         "name": "Greek Salad",
#         "description": "Fresh salad with tomatoes, cucumbers, feta cheese, and olives.",
#         "cuisine": "Greek",
#         "image_url": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg"
#     },
#     {
#         "name": "Pad Thai",
#         "description": "Thai stir-fried noodles with shrimp, peanuts, and lime.",
#         "cuisine": "Thai",
#         "image_url": "https://www.themealdb.com/images/media/meals/uuuspp1511297945.jpg"
#     },
#     {
#         "name": "Falafel Wrap",
#         "description": "Crispy chickpea balls wrapped with vegetables and tahini sauce.",
#         "cuisine": "Middle Eastern",
#         "image_url": "https://www.themealdb.com/images/media/meals/kcv6hj1598733479.jpg"
#     },
#     {
#         "name": "Butter Croissant",
#         "description": "Flaky, buttery French pastry perfect for breakfast.",
#         "cuisine": "French",
#         "image_url": "https://www.themealdb.com/images/media/meals/wpputp1511812960.jpg"
#     },
# ]

# # Upload to Firestore
# for dish in sample_dishes:
#     db.collection("dishes").add(dish)

# print("✅ Sample dishes uploaded to Firestore!")
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred = credentials.Certificate("../serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# # Updated structured data
# sample_dishes = [
#     {
#         "name": "Spaghetti Carbonara",
#         "image_url": "https://www.themealdb.com/images/media/meals/llcbn01574260722.jpg",
#         "tags": ["Pasta", "Italian", "Creamy"],
#         "metadata": {
#             "cuisine": "Italian",
#             "description": "Classic Italian pasta with eggs, cheese, pancetta, and black pepper.",
#             "difficulty": "Medium",
#             "rating": 4.3
#         }
#     },
#     {
#         "name": "Chicken Tikka Masala",
#         "image_url": "https://www.themealdb.com/images/media/meals/wyxwsp1486979827.jpg",
#         "tags": ["Chicken", "Indian", "Spicy"],
#         "metadata": {
#             "cuisine": "Indian",
#             "description": "Chunks of grilled chicken simmered in a creamy spiced tomato sauce.",
#             "difficulty": "Medium",
#             "rating": 4.6
#         }
#     },
#     {
#         "name": "Sushi Platter",
#         "image_url": "https://www.themealdb.com/images/media/meals/g046bb1663960946.jpg",
#         "tags": ["Japanese", "Rice", "Seafood"],
#         "metadata": {
#             "cuisine": "Japanese",
#             "description": "Assorted sushi rolls with fresh fish, vegetables, and rice.",
#             "difficulty": "Hard",
#             "rating": 4.8
#         }
#     },
#     {
#         "name": "Beef Tacos",
#         "image_url": "https://www.themealdb.com/images/media/meals/qtuwxu1468233098.jpg",
#         "tags": ["Taco", "Mexican", "Spicy"],
#         "metadata": {
#             "cuisine": "Mexican",
#             "description": "Crispy taco shells filled with seasoned beef, lettuce, and cheese.",
#             "difficulty": "Easy",
#             "rating": 4.1
#         }
#     },
#     {
#         "name": "Greek Salad",
#         "image_url": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg",
#         "tags": ["Salad", "Greek", "Vegetarian", "Fresh"],
#         "metadata": {
#             "cuisine": "Greek",
#             "description": "Fresh salad with tomatoes, cucumbers, feta cheese, and olives.",
#             "difficulty": "Easy",
#             "rating": 4.5
#         }
#     },
#     {
#         "name": "Pad Thai",
#         "image_url": "https://www.themealdb.com/images/media/meals/uuuspp1511297945.jpg",
#         "tags": ["Thai", "Noodles", "Shrimp"],
#         "metadata": {
#             "cuisine": "Thai",
#             "description": "Thai stir-fried noodles with shrimp, peanuts, and lime.",
#             "difficulty": "Medium",
#             "rating": 4.4
#         }
#     },
#     {
#         "name": "Falafel Wrap",
#         "image_url": "https://www.themealdb.com/images/media/meals/kcv6hj1598733479.jpg",
#         "tags": ["Vegetarian", "Middle Eastern", "Wrap"],
#         "metadata": {
#             "cuisine": "Middle Eastern",
#             "description": "Crispy chickpea balls wrapped with vegetables and tahini sauce.",
#             "difficulty": "Easy",
#             "rating": 4.2
#         }
#     },
#     {
#         "name": "Butter Croissant",
#         "image_url": "https://www.themealdb.com/images/media/meals/wpputp1511812960.jpg",
#         "tags": ["French", "Pastry", "Breakfast"],
#         "metadata": {
#             "cuisine": "French",
#             "description": "Flaky, buttery French pastry perfect for breakfast.",
#             "difficulty": "Medium",
#             "rating": 4.7
#         }
#     },
# ]

# # Upload to Firestore
# for dish in sample_dishes:
#     db.collection("dishes").add(dish)

# print("✅ Structured sample dishes uploaded to Firestore!")


def load_state(uid: str):
    saved_ref = db.collection("recommendation_states").document(uid).get()
    return saved_ref.to_dict()
    return None
print(load_state("ohzcB1bMwKQjBgxwWvGjYcwkPsd2"))

# from datetime import datetime

# def load_state(uid: str):
#     # Reference to user's saved recipes
#     saved_ref = db.collection("userRecipes").document(uid).collection("saved")
#     saved_docs = list(saved_ref.stream())

#     if not saved_docs:
#         return {"saved_recipes": []}

#     saved_recipes = []

#     for doc in saved_docs:
#         saved_data = doc.to_dict()
#         recipe_id = saved_data.get("recipe_id")

#         if not recipe_id:
#             continue

#         # Fetch the actual recipe details from 'dishes' collection
#         recipe_doc = db.collection("dishes").document(recipe_id).get()

#         if not recipe_doc.exists:
#             continue

#         recipe_data = recipe_doc.to_dict()

#         # Combine both recipe details + saved metadata
#         combined_data = {
#             "recipe_id": recipe_id,
#             "name": recipe_data.get("name"),
#             "ingredients": recipe_data.get("ingredients", []),
#             "tags": recipe_data.get("tags", []),
#             "metadata": recipe_data.get("metadata", {}),
#             "saved_at": saved_data.get("saved_at"),
#         }

#         saved_recipes.append(combined_data)


#     return {"saved_recipes": saved_recipes}


# # Example usage:
# print(load_state("ohzcB1bMwKQjBgxwWvGjYcwkPsd2"))
