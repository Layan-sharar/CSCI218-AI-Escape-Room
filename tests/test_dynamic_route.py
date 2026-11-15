
import game.movement as movement

# The robot starts on the level's start cell, (12, 23)
movement.load_level("ember_crypt")

# Save the original route
original_route = movement.route.copy()

# Test 1: Valid route
valid_route = [
    (12, 23),
    (12, 24)
]

result = movement.set_route(valid_route)

print("Test 1 - Valid route:", result)
assert result is True
assert movement.route == valid_route

# Test 2: Empty route
result = movement.set_route([])

print("Test 2 - Empty route:", result)
assert result is False

# Test 3: Non-adjacent route
invalid_route = [
    (12, 23),
    (12, 26)
]

result = movement.set_route(invalid_route)

print("Test 3 - Non-adjacent route:", result)
assert result is False

# Test 4: Incorrect starting position
invalid_start = [
    (12, 24),
    (12, 25)
]

result = movement.set_route(invalid_start)

print("Test 4 - Wrong starting position:", result)
assert result is False

# Restore the original route
assert movement.set_route(original_route) is True

print("\nAll dynamic route tests passed!")
