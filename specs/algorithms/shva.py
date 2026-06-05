"""
Self-Healing Validation Algorithm (SHVA)
=========================================
Automatically detect and correct errors in tax calculations, form completion,
and compliance before client delivery.

Author: Tax God v3.0 System
License: Proprietary
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ValidationStage(Enum):
    """Validation stage types"""
    STRUCTURE = "structure"
    CALCULATION = "calculation"
    COMPLIANCE = "compliance"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"      # Must fix to proceed
    HIGH = "high"              # Should fix
    MEDIUM = "medium"          # Nice to fix
    LOW = "low"                # Optional


@dataclass
class ValidationError:
    """Represents a validation error"""
    stage: ValidationStage
    severity: ErrorSeverity
    field: str
    error_type: str
    message: str
    provided_value: Any = None
    expected_value: Any = None
    formula: Optional[str] = None


@dataclass
class HealingAttempt:
    """Result of an auto-healing attempt"""
    success: bool
    stage: ValidationStage
    corrections_made: List[Dict[str, Any]] = field(default_factory=list)
    iterations: int = 0
    reason: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    result: Dict[str, Any]
    failed_stage: Optional[ValidationStage] = None
    errors: List[ValidationError] = field(default_factory=list)
    healing_log: List[HealingAttempt] = field(default_factory=list)
    requires_human_review: bool = False
    confidence_score: float = 1.0


class SelfHealingValidationAlgorithm:
    """
    SHVA - Multi-stage error detection and auto-correction

    Features:
    - Structure validation
    - Calculation verification
    - Compliance checking
    - Consistency analysis
    - Completeness verification
    - Automatic error correction
    - Confidence scoring
    """

    # Calculated fields with formulas
    CALCULATED_FIELDS = {
        'adjusted_gross_income': 'total_income - adjustments',
        'taxable_income': 'adjusted_gross_income - deductions',
        'total_tax': 'tax_before_credits - credits',
        'amount_owed': 'total_tax - payments',
        'refund_amount': 'payments - total_tax'
    }

    # Required fields for different output types
    REQUIRED_FIELDS = {
        '1040': [
            'filing_status', 'ssn', 'first_name', 'last_name',
            'total_income', 'adjusted_gross_income', 'taxable_income', 'total_tax'
        ],
        '1120': [
            'ein', 'business_name', 'gross_receipts', 'total_deductions',
            'taxable_income', 'total_tax'
        ],
        '1065': [
            'ein', 'partnership_name', 'total_income', 'ordinary_income'
        ]
    }

    # Tax brackets for 2024 (Single)
    TAX_BRACKETS_SINGLE = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ]

    # Standard deduction 2024
    STANDARD_DEDUCTION = {
        'single': 14600,
        'married_filing_jointly': 29200,
        'married_filing_separately': 14600,
        'head_of_household': 21900
    }

    def validate_output(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Main validation pipeline with auto-healing

        Args:
            result: Output to validate (e.g., tax return data)
            output_type: Type of output ('1040', '1120', etc.)
            context: Optional context data

        Returns:
            ValidationResult with healing log
        """
        validation_stages = [
            (ValidationStage.STRUCTURE, self._validate_structure),
            (ValidationStage.CALCULATION, self._validate_calculations),
            (ValidationStage.COMPLIANCE, self._validate_compliance),
            (ValidationStage.CONSISTENCY, self._validate_consistency),
            (ValidationStage.COMPLETENESS, self._validate_completeness)
        ]

        healing_log = []
        current_result = result.copy()

        for stage, validator in validation_stages:
            validation_result = validator(current_result, output_type, context or {})

            if not validation_result['is_valid']:
                # Attempt auto-healing
                healing_attempt = self._attempt_healing(
                    result=current_result,
                    stage=stage,
                    errors=validation_result['errors'],
                    context=context or {}
                )

                healing_log.append(healing_attempt)

                if healing_attempt.success:
                    current_result = healing_attempt.corrections_made[0].get(
                        'corrected_result', current_result
                    ) if healing_attempt.corrections_made else current_result
                else:
                    # Auto-healing failed - escalate to human review
                    return ValidationResult(
                        is_valid=False,
                        result=current_result,
                        failed_stage=stage,
                        errors=validation_result['errors'],
                        healing_log=healing_log,
                        requires_human_review=True,
                        confidence_score=0.0
                    )

        confidence = self._calculate_confidence(healing_log)

        return ValidationResult(
            is_valid=True,
            result=current_result,
            healing_log=healing_log,
            confidence_score=confidence
        )

    def _validate_structure(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify data structure and types"""
        errors = []

        # Check for required fields
        required = self.REQUIRED_FIELDS.get(output_type, [])

        for field in required:  # noqa: F402
            if field not in result or result[field] is None:
                errors.append(ValidationError(
                    stage=ValidationStage.STRUCTURE,
                    severity=ErrorSeverity.CRITICAL,
                    field=field,
                    error_type='missing_field',
                    message=f"Required field '{field}' is missing"
                ))

        # Check data types
        numeric_fields = [
            'total_income', 'adjusted_gross_income', 'taxable_income',
            'total_tax', 'deductions', 'credits'
        ]

        for field in numeric_fields:
            if field in result and result[field] is not None:
                if not isinstance(result[field], (int, float)):
                    errors.append(ValidationError(
                        stage=ValidationStage.STRUCTURE,
                        severity=ErrorSeverity.HIGH,
                        field=field,
                        error_type='invalid_type',
                        message=f"Field '{field}' must be numeric, got {type(result[field]).__name__}",
                        provided_value=result[field]
                    ))

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _validate_calculations(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify mathematical accuracy"""
        errors = []

        if output_type in ['1040', '1120', '1065', 'tax_return']:
            # Check arithmetic consistency
            for field, formula in self.CALCULATED_FIELDS.items():
                if field in result:
                    try:
                        calculated_value = self._evaluate_formula(formula, result)
                        provided_value = result[field]

                        if abs(calculated_value - provided_value) > 1.0:  # $1 tolerance
                            errors.append(ValidationError(
                                stage=ValidationStage.CALCULATION,
                                severity=ErrorSeverity.HIGH,
                                field=field,
                                error_type='calculation_mismatch',
                                message=f"Calculation mismatch for {field}",
                                provided_value=provided_value,
                                expected_value=calculated_value,
                                formula=formula
                            ))
                    except Exception as e:
                        errors.append(ValidationError(
                            stage=ValidationStage.CALCULATION,
                            severity=ErrorSeverity.MEDIUM,
                            field=field,
                            error_type='formula_evaluation_error',
                            message=f"Could not evaluate formula: {str(e)}",
                            formula=formula
                        ))

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _validate_compliance(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check regulatory compliance rules"""
        errors = []

        if output_type == '1040':
            # SSN format check
            if 'ssn' in result:
                if not self._check_ssn_format(result['ssn']):
                    errors.append(ValidationError(
                        stage=ValidationStage.COMPLIANCE,
                        severity=ErrorSeverity.CRITICAL,
                        field='ssn',
                        error_type='invalid_ssn_format',
                        message="SSN must be in format XXX-XX-XXXX",
                        provided_value=result.get('ssn')
                    ))

            # Filing status rules
            if 'filing_status' in result:
                valid_statuses = [
                    'single', 'married_filing_jointly',
                    'married_filing_separately', 'head_of_household',
                    'qualifying_widow'
                ]
                if result['filing_status'] not in valid_statuses:
                    errors.append(ValidationError(
                        stage=ValidationStage.COMPLIANCE,
                        severity=ErrorSeverity.CRITICAL,
                        field='filing_status',
                        error_type='invalid_filing_status',
                        message=f"Filing status must be one of: {', '.join(valid_statuses)}",
                        provided_value=result['filing_status']
                    ))

            # Standard deduction check
            if 'deductions' in result and 'filing_status' in result:
                min_deduction = self.STANDARD_DEDUCTION.get(result['filing_status'], 0)
                if result['deductions'] < min_deduction:
                    errors.append(ValidationError(
                        stage=ValidationStage.COMPLIANCE,
                        severity=ErrorSeverity.MEDIUM,
                        field='deductions',
                        error_type='below_standard_deduction',
                        message=f"Deduction below standard deduction for {result['filing_status']}",
                        provided_value=result['deductions'],
                        expected_value=min_deduction
                    ))

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _validate_consistency(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check internal consistency"""
        errors = []

        # Check that income >= AGI >= taxable income
        if all(k in result for k in ['total_income', 'adjusted_gross_income', 'taxable_income']):
            if result['total_income'] < result['adjusted_gross_income']:
                errors.append(ValidationError(
                    stage=ValidationStage.CONSISTENCY,
                    severity=ErrorSeverity.HIGH,
                    field='adjusted_gross_income',
                    error_type='logical_inconsistency',
                    message="AGI cannot exceed total income"
                ))

            if result['adjusted_gross_income'] < result['taxable_income']:
                errors.append(ValidationError(
                    stage=ValidationStage.CONSISTENCY,
                    severity=ErrorSeverity.HIGH,
                    field='taxable_income',
                    error_type='logical_inconsistency',
                    message="Taxable income cannot exceed AGI"
                ))

        # Check refund vs owed consistency
        if 'refund_amount' in result and 'amount_owed' in result:
            if result['refund_amount'] > 0 and result['amount_owed'] > 0:
                errors.append(ValidationError(
                    stage=ValidationStage.CONSISTENCY,
                    severity=ErrorSeverity.CRITICAL,
                    field='refund_amount',
                    error_type='mutual_exclusivity_violation',
                    message="Cannot have both refund and amount owed"
                ))

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _validate_completeness(
        self,
        result: Dict[str, Any],
        output_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify all necessary data is present"""
        errors = []

        # This overlaps with structure validation but focuses on business logic
        if output_type == '1040':
            # If married filing jointly, need spouse info
            if result.get('filing_status') == 'married_filing_jointly':
                if not result.get('spouse_ssn'):
                    errors.append(ValidationError(
                        stage=ValidationStage.COMPLETENESS,
                        severity=ErrorSeverity.HIGH,
                        field='spouse_ssn',
                        error_type='missing_required_data',
                        message="Spouse SSN required for married filing jointly"
                    ))

            # If claiming dependents, need dependent details
            if result.get('num_dependents', 0) > 0:
                if not result.get('dependent_details'):
                    errors.append(ValidationError(
                        stage=ValidationStage.COMPLETENESS,
                        severity=ErrorSeverity.MEDIUM,
                        field='dependent_details',
                        error_type='missing_supporting_data',
                        message="Dependent details required when claiming dependents"
                    ))

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def _attempt_healing(
        self,
        result: Dict[str, Any],
        stage: ValidationStage,
        errors: List[ValidationError],
        context: Dict[str, Any]
    ) -> HealingAttempt:
        """Attempt automatic error correction"""

        if stage == ValidationStage.CALCULATION:
            return self._heal_calculations(result, errors, context)
        elif stage == ValidationStage.STRUCTURE:
            return self._heal_structure(result, errors, context)
        elif stage == ValidationStage.COMPLIANCE:
            return self._heal_compliance(result, errors, context)
        elif stage == ValidationStage.CONSISTENCY:
            return self._heal_consistency(result, errors, context)
        else:
            return HealingAttempt(
                success=False,
                stage=stage,
                reason='No healing strategy for this stage'
            )

    def _heal_calculations(
        self,
        result: Dict[str, Any],
        errors: List[ValidationError],
        context: Dict[str, Any]
    ) -> HealingAttempt:
        """Auto-correct calculation errors"""
        corrected_result = result.copy()
        corrections_made = []

        for error in errors:
            if error.error_type == 'calculation_mismatch':
                field = error.field
                correct_value = error.expected_value

                # Update field with correct calculation
                corrected_result[field] = correct_value

                corrections_made.append({
                    'field': field,
                    'old_value': error.provided_value,
                    'new_value': correct_value,
                    'formula': error.formula
                })

        # Re-validate calculations
        revalidation = self._validate_calculations(
            corrected_result,
            result.get('form_type', '1040'),
            context
        )

        return HealingAttempt(
            success=revalidation['is_valid'],
            stage=ValidationStage.CALCULATION,
            corrections_made=[{'corrected_result': corrected_result}] if revalidation['is_valid'] else [],
            iterations=1
        )

    def _heal_structure(
        self,
        result: Dict[str, Any],
        errors: List[ValidationError],
        context: Dict[str, Any]
    ) -> HealingAttempt:
        """Auto-correct structure errors"""
        corrected_result = result.copy()
        corrections_made = []

        for error in errors:
            if error.error_type == 'invalid_type':
                try:
                    # Attempt type conversion
                    corrected_result[error.field] = float(error.provided_value)
                    corrections_made.append({
                        'field': error.field,
                        'action': 'type_conversion',
                        'old_value': error.provided_value,
                        'new_value': corrected_result[error.field]
                    })
                except Exception:
                    return HealingAttempt(
                        success=False,
                        stage=ValidationStage.STRUCTURE,
                        reason=f"Cannot convert {error.field} to numeric type"
                    )

        return HealingAttempt(
            success=len(corrections_made) > 0,
            stage=ValidationStage.STRUCTURE,
            corrections_made=[{'corrected_result': corrected_result}] if corrections_made else [],
            iterations=1
        )

    def _heal_compliance(
        self,
        result: Dict[str, Any],
        errors: List[ValidationError],
        context: Dict[str, Any]
    ) -> HealingAttempt:
        """Auto-correct compliance errors"""
        # Most compliance errors require human intervention
        # But some can be auto-fixed

        corrected_result = result.copy()
        corrections_made = []

        for error in errors:
            if error.error_type == 'below_standard_deduction':
                # Auto-upgrade to standard deduction
                corrected_result[error.field] = error.expected_value
                corrections_made.append({
                    'field': error.field,
                    'action': 'upgraded_to_standard_deduction',
                    'old_value': error.provided_value,
                    'new_value': error.expected_value
                })

        return HealingAttempt(
            success=len(corrections_made) > 0,
            stage=ValidationStage.COMPLIANCE,
            corrections_made=[{'corrected_result': corrected_result}] if corrections_made else [],
            iterations=1,
            reason='Some compliance errors require manual review' if not corrections_made else None
        )

    def _heal_consistency(
        self,
        result: Dict[str, Any],
        errors: List[ValidationError],
        context: Dict[str, Any]
    ) -> HealingAttempt:
        """Auto-correct consistency errors"""
        # Consistency errors usually indicate deeper issues
        # Mark for human review
        return HealingAttempt(
            success=False,
            stage=ValidationStage.CONSISTENCY,
            reason='Consistency errors require manual review'
        )

    def _calculate_confidence(self, healing_log: List[HealingAttempt]) -> float:
        """
        Confidence score based on healing complexity

        Args:
            healing_log: List of healing attempts

        Returns:
            Confidence score (0.5 - 1.0)
        """
        if len(healing_log) == 0:
            return 1.0  # No healing needed = perfect confidence

        healing_complexity = sum([
            0.05 for h in healing_log if h.success
        ]) + sum([
            0.20 for h in healing_log if not h.success
        ])

        return max(0.5, 1.0 - healing_complexity)

    def _evaluate_formula(self, formula: str, data: Dict[str, Any]) -> float:
        """
        Safely evaluate a formula with data

        Args:
            formula: Formula string (e.g., 'total_income - adjustments')
            data: Data dictionary

        Returns:
            Calculated value
        """
        # Replace field names with values
        formula_eval = formula
        for field, value in data.items():  # noqa: F402
            if isinstance(value, (int, float)):
                formula_eval = formula_eval.replace(field, str(value))

        # Safe evaluation (only allow basic math)
        try:
            # Remove any remaining field names (treat as 0)
            formula_eval = re.sub(r'[a-zA-Z_]\w*', '0', formula_eval)
            return eval(formula_eval, {"__builtins__": {}}, {})
        except Exception:
            raise ValueError(f"Cannot evaluate formula: {formula}")

    def _check_ssn_format(self, ssn: str) -> bool:
        """Check if SSN is in valid format"""
        pattern = r'^\d{3}-\d{2}-\d{4}$'
        return bool(re.match(pattern, str(ssn)))


# Example usage
if __name__ == "__main__":
    shva = SelfHealingValidationAlgorithm()

    # Test 1: Valid return
    valid_return = {
        'form_type': '1040',
        'filing_status': 'single',
        'ssn': '123-45-6789',
        'first_name': 'John',
        'last_name': 'Doe',
        'total_income': 95000,
        'adjustments': 5000,
        'adjusted_gross_income': 90000,
        'deductions': 14600,  # Standard deduction
        'taxable_income': 75400,
        'total_tax': 12500,
        'credits': 0,
        'payments': 13000,
        'refund_amount': 500,
        'amount_owed': 0
    }

    result1 = shva.validate_output(valid_return, '1040')
    print("Test 1 - Valid Return:")
    print(f"  Valid: {result1.is_valid}")
    print(f"  Confidence: {result1.confidence_score:.2f}")
    print(f"  Healing attempts: {len(result1.healing_log)}")
    print()

    # Test 2: Return with calculation error
    error_return = {
        'form_type': '1040',
        'filing_status': 'single',
        'ssn': '123-45-6789',
        'first_name': 'Jane',
        'last_name': 'Smith',
        'total_income': 85000,
        'adjustments': 3000,
        'adjusted_gross_income': 82000,  # Correct
        'deductions': 14600,
        'taxable_income': 60000,  # WRONG! Should be 67400
        'total_tax': 10000,
        'credits': 0,
        'payments': 11000,
        'refund_amount': 1000,
        'amount_owed': 0
    }

    result2 = shva.validate_output(error_return, '1040')
    print("Test 2 - Return with Calculation Error:")
    print(f"  Valid: {result2.is_valid}")
    print(f"  Confidence: {result2.confidence_score:.2f}")
    print(f"  Healing attempts: {len(result2.healing_log)}")
    if result2.healing_log:
        for heal in result2.healing_log:
            print(f"  - Stage: {heal.stage.value}, Success: {heal.success}")
            if heal.corrections_made:
                print(f"    Corrections: {len(heal.corrections_made)}")
    print()
