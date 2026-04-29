def rank_cars(cars, parsed_query):
	"""Rank cars combining DB constraint matching + FAISS semantic scores.

	Args:
		cars: list of dicts with DB car data and optional 'faiss_score' key
		parsed_query: dict from parser with constraints

	Returns:
		sorted list of cars with combined scores
	"""
	ranked = []

	budget_max = parsed_query.get("budget_max")
	fuel_types = parsed_query.get("fuel_types", [])
	body_styles = parsed_query.get("body_styles", [])
	seating_min = parsed_query.get("seating_min")
	transmission = parsed_query.get("transmission")

	for car in cars:
		score = 0.0

		# Constraint satisfaction score (binary: match or not)
		constraint_score = 0.0
		num_constraints = 0

		# Budget: bonus if under budget, penalty if over
		if budget_max is not None:
			num_constraints += 1
			if car.get("price_max", 0) <= budget_max:
				constraint_score += 1.0
			else:
				# Penalize overage: small bonus if close, penalty if far
				overage_ratio = car.get("price_max", budget_max) / budget_max
				if overage_ratio < 1.2:  # Within 20% of budget
					constraint_score += 0.3

		# Fuel type match
		if fuel_types:
			num_constraints += 1
			if car.get("fuel_type", "").lower() in fuel_types:
				constraint_score += 1.0

		# Body type match
		if body_styles:
			num_constraints += 1
			if car.get("body_type", "").lower() in body_styles:
				constraint_score += 1.0

		# Seating
		if seating_min is not None:
			num_constraints += 1
			if car.get("seats", 0) >= seating_min:
				constraint_score += 1.0
			else:
				constraint_score += 0.5  # Partial credit

		# Transmission
		if transmission:
			num_constraints += 1
			if car.get("transmission", "").lower() == transmission:
				constraint_score += 1.0

		# Normalize constraint score by number of constraints
		if num_constraints > 0:
			constraint_score = constraint_score / num_constraints
		else:
			constraint_score = 0.5  # Default if no constraints

		# FAISS semantic relevance score (if provided)
		faiss_score = car.get("faiss_score", 0.0)

		# Safety bonus
		safety_rating = car.get("safety_rating", 4.0)
		safety_score = min(safety_rating / 5.0, 1.0)  # Normalize to [0,1]

		# Combine scores: 60% constraints, 30% FAISS, 10% safety
		score = (0.6 * constraint_score) + (0.3 * faiss_score) + (0.1 * safety_score)

		car["score"] = score
		car["constraint_score"] = constraint_score
		car["faiss_score"] = faiss_score
		ranked.append(car)

	return sorted(ranked, key=lambda x: x["score"], reverse=True)