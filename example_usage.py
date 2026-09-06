"""
Demonstration of genpark-autonomous-test-mutation-coverage-scorer-skill
"""

from client import TestMutationCoverageScorerClient

def main():
    client = TestMutationCoverageScorerClient()

    source_code = """
def is_eligible_discount(age, is_member):
    if age >= 65 or is_member == True:
        return True
    return False
"""

    # Test cases that lack boundary checking (fails to test age == 65 specifically)
    weak_test_cases = [
        {"fn_name": "is_eligible_discount", "args": [70, False], "expected": True},
        {"fn_name": "is_eligible_discount", "args": [30, False], "expected": False}
    ]

    res = client.evaluate_mutation_score(source_code, weak_test_cases)
    print("=== MUTATION TESTING SCORE REPORT ===")
    print(f"Mutation Score Indicator (MSI): {res['msi']}%")
    print(f"Total Mutants: {res['total_mutants']} | Killed: {res['killed_mutants']} | Survived: {res['survived_mutants']}")
    for d in res['details']:
        print(f"  [{d['status']}] {d['mutant_id']}: {d.get('reason', 'Mutant survived test suite!')}")

if __name__ == "__main__":
    main()
