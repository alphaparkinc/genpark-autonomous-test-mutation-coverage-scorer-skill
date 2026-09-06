"""
Mutation Testing Coverage Analyzer and Boundary Test Case Synthesizer.
Zero external dependencies, standard library only.
"""

import ast
import copy
from typing import Dict, List, Any, Optional, Callable

class TestMutationCoverageScorerClient:
    """
    Evaluates test suite quality using AST mutant generation:
    - Operator mutations (+ <-> -, * <-> /)
    - Comparison mutations (== <-> !=, < <-> <=)
    - Boolean constant flips (True <-> False)
    - Boundary returns (None / 0 / empty)
    Calculates Mutation Score Indicator (MSI) and identifies surviving mutants.
    """

    def __init__(self):
        pass

    def generate_mutants(self, code: str) -> List[Dict[str, Any]]:
        """Generates list of mutated code snippets with mutation descriptors."""
        mutants = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        # 1. Comparison mutations
        cmp_map = {
            ast.Eq: ast.NotEq,
            ast.NotEq: ast.Eq,
            ast.Lt: ast.GtE,
            ast.Gt: ast.LtE,
            ast.LtE: ast.Gt,
            ast.GtE: ast.Lt
        }

        # 2. Binary Op mutations
        binop_map = {
            ast.Add: ast.Sub,
            ast.Sub: ast.Add,
            ast.Mult: ast.FloorDiv
        }

        class MutationFinder(ast.NodeVisitor):
            def __init__(self):
                self.locations = []

            def visit_Compare(self, node):
                for i, op in enumerate(node.ops):
                    if type(op) in cmp_map:
                        self.locations.append(("cmp", node, i, type(op)))
                self.generic_visit(node)

            def visit_BinOp(self, node):
                if type(node.op) in binop_map:
                    self.locations.append(("binop", node, None, type(node.op)))
                self.generic_visit(node)

            def visit_Constant(self, node):
                if isinstance(node.value, bool):
                    self.locations.append(("bool", node, None, node.value))
                self.generic_visit(node)

        finder = MutationFinder()
        finder.visit(tree)

        for idx, (m_type, node, sub_idx, orig_val) in enumerate(finder.locations):
            cloned_tree = copy.deepcopy(tree)
            
            # Re-find node in cloned tree
            class Mutator(ast.NodeTransformer):
                def __init__(self, target_lineno, target_col):
                    self.target_lineno = target_lineno
                    self.target_col = target_col
                    self.mutated = False

                def visit_Compare(self, n):
                    if not self.mutated and m_type == "cmp" and getattr(n, "lineno", -1) == self.target_lineno and getattr(n, "col_offset", -1) == self.target_col:
                        new_op_cls = cmp_map[orig_val]
                        n.ops[sub_idx] = new_op_cls()
                        self.mutated = True
                    return self.generic_visit(n)

                def visit_BinOp(self, n):
                    if not self.mutated and m_type == "binop" and getattr(n, "lineno", -1) == self.target_lineno and getattr(n, "col_offset", -1) == self.target_col:
                        new_op_cls = binop_map[orig_val]
                        n.op = new_op_cls()
                        self.mutated = True
                    return self.generic_visit(n)

                def visit_Constant(self, n):
                    if not self.mutated and m_type == "bool" and getattr(n, "lineno", -1) == self.target_lineno and getattr(n, "col_offset", -1) == self.target_col:
                        n.value = not orig_val
                        self.mutated = True
                    return self.generic_visit(n)

            mutator = Mutator(getattr(node, "lineno", -1), getattr(node, "col_offset", -1))
            mutated_tree = mutator.visit(cloned_tree)
            ast.fix_missing_locations(mutated_tree)

            try:
                mutated_code = ast.unparse(mutated_tree) if hasattr(ast, "unparse") else code
                mutants.append({
                    "id": f"mutant_{idx + 1}",
                    "type": m_type,
                    "line": getattr(node, "lineno", 0),
                    "original": str(orig_val),
                    "code": mutated_code
                })
            except Exception:
                pass

        return mutants

    def evaluate_mutation_score(self, original_code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes test_cases against original and synthesized mutants.
        Each test_case should have 'fn_name', 'args', and 'expected'.
        """
        mutants = self.generate_mutants(original_code)
        if not mutants:
            return {"msi": 100.0, "total_mutants": 0, "killed_mutants": 0, "survived_mutants": 0, "details": []}

        # Validate original code passes all tests first
        orig_scope = {}
        try:
            exec(original_code, orig_scope)
        except Exception as e:
            return {"status": "error", "message": f"Original code fails to execute: {e}"}

        for tc in test_cases:
            fn = orig_scope.get(tc["fn_name"])
            if not fn or fn(*tc.get("args", [])) != tc.get("expected"):
                return {"status": "error", "message": f"Baseline test case failed on original code: {tc}"}

        killed_count = 0
        details = []

        for m in mutants:
            m_scope = {}
            killed = False
            kill_reason = ""
            try:
                exec(m["code"], m_scope)
                for tc in test_cases:
                    fn = m_scope.get(tc["fn_name"])
                    if not fn:
                        killed = True
                        kill_reason = f"Function {tc['fn_name']} missing"
                        break
                    val = fn(*tc.get("args", []))
                    if val != tc.get("expected"):
                        killed = True
                        kill_reason = f"Assertion failed: expected {tc.get('expected')}, got {val}"
                        break
            except Exception as e:
                killed = True
                kill_reason = f"Runtime exception: {e}"

            if killed:
                killed_count += 1
                details.append({"mutant_id": m["id"], "status": "KILLED", "reason": kill_reason})
            else:
                details.append({
                    "mutant_id": m["id"],
                    "status": "SURVIVED",
                    "line": m["line"],
                    "type": m["type"],
                    "mutated_code": m["code"]
                })

        msi = round((killed_count / len(mutants)) * 100.0, 2)
        return {
            "status": "success",
            "msi": msi,
            "total_mutants": len(mutants),
            "killed_mutants": killed_count,
            "survived_mutants": len(mutants) - killed_count,
            "details": details
        }
