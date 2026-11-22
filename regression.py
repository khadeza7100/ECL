import math


def _beta_continued_fraction(a, b, x):
    max_iterations = 200
    epsilon = 3e-14
    minimum_value = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < minimum_value:
        d = minimum_value
    d = 1.0 / d
    result = d

    for iteration in range(1, max_iterations + 1):
        twice_iteration = 2 * iteration
        coefficient = (
            iteration * (b - iteration) * x
            / ((qam + twice_iteration) * (a + twice_iteration))
        )
        d = 1.0 + coefficient * d
        if abs(d) < minimum_value:
            d = minimum_value
        c = 1.0 + coefficient / c
        if abs(c) < minimum_value:
            c = minimum_value
        d = 1.0 / d
        result *= d * c

        coefficient = (
            -(a + iteration) * (qab + iteration) * x
            / ((a + twice_iteration) * (qap + twice_iteration))
        )
        d = 1.0 + coefficient * d
        if abs(d) < minimum_value:
            d = minimum_value
        c = 1.0 + coefficient / c
        if abs(c) < minimum_value:
            c = minimum_value
        d = 1.0 / d
        delta = d * c
        result *= delta
        if abs(delta - 1.0) < epsilon:
            return result

    raise ArithmeticError("Incomplete beta calculation did not converge.")


def _regularized_incomplete_beta(x, a, b):
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    log_front = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )
    front = math.exp(log_front)
    if x < (a + 1.0) / (a + b + 2.0):
        value = front * _beta_continued_fraction(a, b, x) / a
    else:
        value = 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b
    return min(1.0, max(0.0, value))


def two_sided_t_p_value(t_statistic, degrees_of_freedom):
    if degrees_of_freedom <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if math.isinf(t_statistic):
        return 0.0
    beta_argument = degrees_of_freedom / (
        degrees_of_freedom + t_statistic * t_statistic
    )
    return _regularized_incomplete_beta(
        beta_argument,
        degrees_of_freedom / 2.0,
        0.5,
    )


def _invert_matrix(matrix):
    size = len(matrix)
    augmented = [
        row[:] + [1.0 if row_index == column else 0.0 for column in range(size)]
        for row_index, row in enumerate(matrix)
    ]

    for column in range(size):
        pivot_row = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot_row][column]) < 1e-12:
            return None
        augmented[column], augmented[pivot_row] = augmented[pivot_row], augmented[column]

        pivot = augmented[column][column]
        augmented[column] = [value / pivot for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            multiplier = augmented[row][column]
            augmented[row] = [
                value - multiplier * pivot_value
                for value, pivot_value in zip(augmented[row], augmented[column])
            ]

    return [row[size:] for row in augmented]


def fit_multiple_regression(predictor_names, predictor_rows, outcomes):
    predictor_count = len(predictor_names)
    observation_count = len(outcomes)
    degrees_of_freedom = observation_count - predictor_count - 1
    if degrees_of_freedom <= 0 or len(predictor_rows) != observation_count:
        return None

    means = [
        sum(row[column] for row in predictor_rows) / observation_count
        for column in range(predictor_count)
    ]
    standard_deviations = []
    for column, mean in enumerate(means):
        variance = sum(
            (row[column] - mean) ** 2 for row in predictor_rows
        ) / observation_count
        if variance <= 1e-24:
            return None
        standard_deviations.append(math.sqrt(variance))

    design = [
        [1.0] + [
            (row[column] - means[column]) / standard_deviations[column]
            for column in range(predictor_count)
        ]
        for row in predictor_rows
    ]
    column_count = predictor_count + 1
    xtx = [
        [
            sum(row[left] * row[right] for row in design)
            for right in range(column_count)
        ]
        for left in range(column_count)
    ]
    inverse = _invert_matrix(xtx)
    if inverse is None:
        return None

    xty = [
        sum(row[column] * outcome for row, outcome in zip(design, outcomes))
        for column in range(column_count)
    ]
    coefficients = [
        sum(inverse[row][column] * xty[column] for column in range(column_count))
        for row in range(column_count)
    ]
    residual_sum_squares = sum(
        (
            outcome
            - sum(value * coefficient for value, coefficient in zip(row, coefficients))
        ) ** 2
        for row, outcome in zip(design, outcomes)
    )
    mean_squared_error = residual_sum_squares / degrees_of_freedom
    outcome_mean = sum(outcomes) / observation_count
    total_sum_squares = sum((outcome - outcome_mean) ** 2 for outcome in outcomes)
    r_squared = (
        min(1.0, max(0.0, 1.0 - residual_sum_squares / total_sum_squares))
        if total_sum_squares > 0
        else None
    )
    results = []

    for index, variable in enumerate(predictor_names, start=1):
        coefficient = coefficients[index]
        coefficient_variance = mean_squared_error * inverse[index][index]
        if coefficient_variance < 0:
            return None
        if coefficient_variance == 0:
            t_statistic = 0.0 if coefficient == 0 else math.copysign(math.inf, coefficient)
        else:
            t_statistic = coefficient / math.sqrt(coefficient_variance)
        results.append({
            "variable": variable,
            "coefficient": coefficient,
            "t_statistic": t_statistic,
            "p_value": two_sided_t_p_value(t_statistic, degrees_of_freedom),
        })

    return {
        "degrees_of_freedom": degrees_of_freedom,
        "r_squared": r_squared,
        "intercept": coefficients[0],
        "predictor_means": means,
        "predictor_standard_deviations": standard_deviations,
        "predictor_coefficients": coefficients[1:],
        "results": results,
    }


def predict_multiple_regression(model, predictor_values):
    if model is None or len(predictor_values) != len(model["predictor_means"]):
        return None

    standardized_values = [
        (value - mean) / standard_deviation
        for value, mean, standard_deviation in zip(
            predictor_values,
            model["predictor_means"],
            model["predictor_standard_deviations"],
        )
    ]
    return model["intercept"] + sum(
        value * coefficient
        for value, coefficient in zip(
            standardized_values,
            model["predictor_coefficients"],
        )
    )
