"""
JSON-Driven Validator
=====================
Simple validator that reads validation rules from a JSON file.

Usage:
    from json_driven_validator import JSONValidator

    # Load rules from JSON file
    validator = JSONValidator('validation_rules.json')

    # Validate loan terms
    warnings, errors = validator.validate(loan_terms)

    # Or validate with custom rules
    custom_rules = {...}
    warnings, errors = validator.validate(loan_terms, custom_rules)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add reference code path
_current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_current_dir, 'reference code'))
from step99 import get_loan_terms_metadata


class JSONValidator:
    """Validator that executes rules from JSON configuration."""

    def __init__(self, rules_file: str = 'validation_rules.json'):
        """
        Initialize validator with rules file.

        Args:
            rules_file: Path to JSON file containing validation rules
        """
        # If rules_file is relative, make it relative to this module's directory
        if not os.path.isabs(rules_file):
            _current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_file = os.path.join(_current_dir, rules_file)

        self.rules_file = rules_file
        self.metadata = get_loan_terms_metadata()
        self._metadata_lookup = self._build_metadata_lookup()

    def _build_metadata_lookup(self) -> Dict[str, str]:
        """Build quick lookup for field display names."""
        lookup = {}
        for meta in self.metadata:
            key = f"{meta['TABLE']}:{meta['FIELD']}"
            lookup[key] = meta['DISPLAYNAME']
        return lookup

    def _get_display_name(self, table: str, field: str) -> str:
        """Get display name for a field."""
        key = f"{table}:{field}"
        return self._metadata_lookup.get(key, field)

    def load_rules(self, rules_file: Optional[str] = None) -> Dict[str, Any]:
        """Load validation rules from JSON file."""
        file_path = rules_file or self.rules_file
        with open(file_path, 'r') as f:
            return json.load(f)

    def validate(
        self,
        loan_terms: Dict[str, Any],
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate loan terms using rules from JSON.

        Args:
            loan_terms: Loan data to validate
            custom_rules: Optional custom rules (if not provided, loads from file)

        Returns:
            Tuple of (warnings, errors)
        """
        # Load rules
        if custom_rules:
            rules_data = custom_rules
        else:
            rules_data = self.load_rules()

        warnings = []
        errors = []

        # Execute each rule
        for rule in rules_data.get('validation_rules', []):
            # Skip if disabled
            if not rule.get('enabled', True):
                continue

            # Execute based on test type
            test_type = rule['test_type']
            entity = rule['entity']

            if test_type == 'required_fields':
                self._validate_required_fields(loan_terms, rule, warnings, errors)

            elif test_type == 'date_format':
                self._validate_date_format(loan_terms, rule, warnings, errors)

            elif test_type == 'amount_format':
                self._validate_amount_format(loan_terms, rule, warnings, errors)

            elif test_type == 'date_relationship':
                self._validate_date_relationship(loan_terms, rule, warnings, errors)

            elif test_type == 'array_exists':
                self._validate_array_exists(loan_terms, rule, warnings, errors)

            elif test_type == 'conditional_required':
                self._validate_conditional_required(loan_terms, rule, warnings, errors)

            elif test_type == 'conditional_warning':
                self._validate_conditional_warning(loan_terms, rule, warnings, errors)

            elif test_type == 'sum_validation':
                self._validate_sum(loan_terms, rule, warnings, errors)

            elif test_type == 'date_match':
                self._validate_date_match(loan_terms, rule, warnings, errors)

        return warnings, errors

    def _add_message(self, buffer: List[Dict], table: str, record_id: Optional[str],
                     field: Optional[str], message: str):
        """Add a validation message to buffer."""
        buffer.append({
            'TABLE': table,
            'ID': record_id,
            'FIELD': field,
            'MESSAGE': message
        })

    def _get_records(self, loan_terms: Dict[str, Any], entity: str) -> List[Dict]:
        """Get records for entity."""
        if entity == 'LOAN_INFO':
            return [loan_terms]
        else:
            array_name = f"{entity}_DETAILS"
            return loan_terms.get(array_name, [])

    def _should_exclude(self, record: Dict[str, Any], exclude_when: Optional[Dict]) -> bool:
        """Check if record should be excluded based on condition."""
        if not exclude_when:
            return False

        field = exclude_when.get('field')
        value = exclude_when.get('value')

        if field and value:
            record_value = record.get(field, '').lower()
            expected_value = value.lower()
            return record_value == expected_value

        return False

    # ========================================================================
    # Validation Methods
    # ========================================================================

    def _validate_required_fields(self, loan_terms: Dict, rule: Dict,
                                   warnings: List, errors: List):
        """Validate required fields."""
        entity = rule['entity']
        fields = rule['fields']
        severity = rule['severity']
        exclude_when = rule.get('exclude_when')

        buffer = errors if severity == 'error' else warnings
        records = self._get_records(loan_terms, entity)

        for record in records:
            # Skip if excluded
            if self._should_exclude(record, exclude_when):
                continue

            for field in fields:
                if field not in record:
                    display_name = self._get_display_name(entity, field)
                    message = f'"{display_name}" is required.'
                    self._add_message(buffer, entity, record.get('ID'), field, message)

    def _validate_date_format(self, loan_terms: Dict, rule: Dict,
                              warnings: List, errors: List):
        """Validate date format."""
        entity = rule['entity']
        fields = rule['fields']
        date_format = rule.get('format', '%Y-%m-%d')
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings
        records = self._get_records(loan_terms, entity)

        for record in records:
            for field in fields:
                if field in record:
                    try:
                        datetime.strptime(record[field], date_format)
                    except ValueError as e:
                        display_name = self._get_display_name(entity, field)
                        user_msg = str(e).replace('%Y-%m-%d', 'YYYY-MM-DD')
                        message = f'"{display_name}" has a problem: {user_msg}.'
                        self._add_message(buffer, entity, record.get('ID'), field, message)

    def _validate_amount_format(self, loan_terms: Dict, rule: Dict,
                                warnings: List, errors: List):
        """Validate amount format."""
        entity = rule['entity']
        fields = rule['fields']
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings
        records = self._get_records(loan_terms, entity)

        for record in records:
            for field in fields:
                if field in record:
                    try:
                        float(record[field])
                    except (ValueError, TypeError):
                        display_name = self._get_display_name(entity, field)
                        message = f'"{display_name}" must be a valid numeric value.'
                        self._add_message(buffer, entity, record.get('ID'), field, message)

    def _validate_date_relationship(self, loan_terms: Dict, rule: Dict,
                                    warnings: List, errors: List):
        """Validate date relationship."""
        entity = rule['entity']
        field1 = rule['field1']
        field2 = rule['field2']
        operator = rule['operator']
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings
        records = self._get_records(loan_terms, entity)

        operator_map = {
            'less_than': '<',
            'less_than_or_equal': '<=',
            'greater_than': '>',
            'greater_than_or_equal': '>=',
            'equal': '=='
        }

        operator_text_map = {
            'less_than': 'before',
            'less_than_or_equal': 'before or same as',
            'greater_than': 'after',
            'greater_than_or_equal': 'after or same as',
            'equal': 'same as'
        }

        for record in records:
            if field1 in record and field2 in record:
                try:
                    dt1 = datetime.strptime(record[field1], '%Y-%m-%d').date()
                    dt2 = datetime.strptime(record[field2], '%Y-%m-%d').date()

                    # Check relationship
                    op_symbol = operator_map.get(operator, '<')
                    valid = eval(f"dt1 {op_symbol} dt2")

                    if not valid:
                        display1 = self._get_display_name(entity, field1)
                        display2 = self._get_display_name(entity, field2)
                        op_text = operator_text_map.get(operator, 'before')
                        message = f"{display1} ({dt1}) is supposed to be {op_text} {display2} ({dt2}). But it is not"
                        self._add_message(buffer, entity, record.get('ID'), field1, message)

                except (ValueError, KeyError):
                    # Skip if dates are invalid (handled by format validator)
                    pass

    def _validate_array_exists(self, loan_terms: Dict, rule: Dict,
                               warnings: List, errors: List):
        """Validate that arrays exist and have data."""
        arrays = rule['arrays']
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings

        for array_name in arrays:
            if array_name not in loan_terms or len(loan_terms[array_name]) == 0:
                message = f"{array_name.replace('_', ' ').title()} are required."
                self._add_message(buffer, 'LOAN_INFO', None, None, message)

    def _validate_conditional_required(self, loan_terms: Dict, rule: Dict,
                                       warnings: List, errors: List):
        """Validate conditionally required fields."""
        entity = rule['entity']
        condition_field = rule['condition_field']
        condition_value = rule.get('condition_value')
        condition_value_not = rule.get('condition_value_not')
        condition_contains = rule.get('condition_contains')
        required_fields = rule['required_fields']
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings
        records = self._get_records(loan_terms, entity)

        for record in records:
            if condition_field in record:
                # Check condition
                meets_condition = False

                if condition_value:
                    meets_condition = record[condition_field] == condition_value
                elif condition_value_not:
                    meets_condition = record[condition_field] != condition_value_not
                elif condition_contains:
                    record_value = str(record.get(condition_field, '')).lower()
                    meets_condition = condition_contains.lower() in record_value

                # If condition met, check required fields
                if meets_condition:
                    for required_field in required_fields:
                        if required_field not in record:
                            display_name = self._get_display_name(entity, required_field)
                            message = f'"{display_name}" is required based on the {condition_field} value.'
                            self._add_message(buffer, entity, record.get('ID'), required_field, message)

    def _validate_conditional_warning(self, loan_terms: Dict, rule: Dict,
                                      warnings: List, errors: List):
        """Validate conditional warnings (for floating rate)."""
        entity = rule['entity']
        condition_field = rule['condition_field']
        condition_value_not = rule.get('condition_value_not')
        check_fields = rule['check_fields']
        severity = rule['severity']

        buffer = warnings  # Always warnings
        records = self._get_records(loan_terms, entity)

        default_messages = {
            'LLC_BI__RATE_FLOOR__C': '0% floor will be assumed',
            'LLC_BI__RATE_CEILING__C': 'There will be no ceiling',
            'LLC_BI__SPREAD__C': '0% Spread will be assumed'
        }

        for record in records:
            if condition_field in record:
                # Check condition
                if condition_value_not:
                    meets_condition = record[condition_field] != condition_value_not

                    if meets_condition:
                        for check_field in check_fields:
                            if check_field not in record:
                                display_name = self._get_display_name(entity, check_field)
                                default_msg = default_messages.get(check_field, '')
                                message = f"{display_name} is required for Floating Rate pricing. {default_msg}"
                                self._add_message(buffer, entity, record.get('ID'), check_field, message)

    def _validate_sum(self, loan_terms: Dict, rule: Dict,
                     warnings: List, errors: List):
        """Validate sum of amounts."""
        entity = rule['entity']
        sum_field = rule['sum_field']
        equals_field = rule['equals_field']
        equals_entity = rule['equals_entity']
        tolerance = rule.get('tolerance', 0.01)
        exclude_when = rule.get('exclude_when')
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings

        # Get target amount
        if equals_entity == 'LOAN_INFO':
            if equals_field not in loan_terms:
                return
            target_amount = float(loan_terms[equals_field])
        else:
            return

        # Calculate sum
        records = self._get_records(loan_terms, entity)
        total = 0.0

        for record in records:
            # Skip if excluded
            if self._should_exclude(record, exclude_when):
                continue

            if sum_field in record:
                try:
                    total += float(record[sum_field])
                except (ValueError, TypeError):
                    pass

        # Check if sum matches
        if abs(total - target_amount) > tolerance:
            message = f"Total draw amounts (${total:,.2f}) do not add up to total loan amount (${target_amount:,.2f})"
            self._add_message(buffer, entity, None, None, message)

    def _validate_date_match(self, loan_terms: Dict, rule: Dict,
                            warnings: List, errors: List):
        """Validate cross-entity date matching."""
        source_entity = rule['source_entity']
        source_field = rule['source_field']
        target_entity = rule['target_entity']
        target_field = rule['target_field']
        match_requirement = rule.get('match_requirement', 'at_least_one')
        severity = rule['severity']

        buffer = errors if severity == 'error' else warnings

        # Get source date
        if source_entity == 'LOAN_INFO':
            if source_field not in loan_terms:
                return
            source_date = loan_terms[source_field]
        else:
            return

        # Check target records
        target_array = f"{target_entity}_DETAILS"
        if target_array not in loan_terms:
            return

        matches_found = 0
        for record in loan_terms[target_array]:
            if target_field in record and record[target_field] == source_date:
                matches_found += 1

        # Check match requirement
        if match_requirement == 'at_least_one' and matches_found == 0:
            display_source = self._get_display_name('LOAN_INFO', source_field)
            message = f"At least one {target_entity} stream should start on the {display_source}, but none do"
            self._add_message(buffer, 'LOAN_INFO', None, None, message)


if __name__ == "__main__":
    """
    Usage Examples:

    1. Validate by Loan ID:
       python json_driven_validator.py a0ial00000364X3AAI

    2. Validate by Loan Name:
       python json_driven_validator.py "Canyon Valley - Mezz"

    3. Search and validate:
       python json_driven_validator.py --search "Canyon"
    """
    import sys
    import os

    # Ensure we can import from core directory
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    if _current_dir not in sys.path:
        sys.path.insert(0, _current_dir)

    from salesforce_fetcher import SalesforceFetcher
    from config import SALESFORCE_CREDENTIALS

    # Parse command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  By ID:     python json_driven_validator.py <LOAN_ID>")
        print("  By Name:   python json_driven_validator.py \"<LOAN_NAME>\"")
        print("  Search:    python json_driven_validator.py --search <PREFIX>")
        print("\nExample:")
        print("  python json_driven_validator.py a0ial00000364X3AAI")
        print("  python json_driven_validator.py \"Canyon Valley - Mezz\"")
        print("  python json_driven_validator.py --search Canyon\n")
        sys.exit(1)

    fetcher = SalesforceFetcher(**SALESFORCE_CREDENTIALS)

    # Handle search mode
    if sys.argv[1] == "--search":
        if len(sys.argv) < 3:
            print("Error: Please provide a search prefix")
            sys.exit(1)

        search_term = sys.argv[2]
        print(f"\n{'='*70}")
        print(f"Searching for loans: {search_term}")
        print(f"{'='*70}\n")

        loans = fetcher.search_loans(name_prefix=search_term)
        print(f"Found {len(loans)} loan(s):\n")
        for i, loan in enumerate(loans, 1):
            print(f"{i}. {loan['NAME']}")
            print(f"   ID: {loan['ID']}\n")
        sys.exit(0)

    # Determine if argument is ID or name
    loan_identifier = sys.argv[1]

    print(f"\n{'='*70}")
    print(f"Fetching and Validating Loan")
    print(f"{'='*70}\n")

    try:
        # Try fetching by ID first
        if loan_identifier.startswith('a0'):
            print(f"Fetching by ID: {loan_identifier}")
            loan_terms = fetcher.get_loan_terms_by_id(loan_identifier)
        else:
            print(f"Fetching by name: {loan_identifier}")
            loan_terms = fetcher.get_loan_terms_by_name(loan_identifier, exact_match=True)

        # Display loan info
        print(f"\n✓ Fetched: {loan_terms['NAME']}")
        print(f"  ID: {loan_terms['ID']}")
        print(f"  Amount: ${loan_terms.get('LLC_BI__AMOUNT__C', 0):,.2f}")
        print(f"  Close Date: {loan_terms.get('LLC_BI__CLOSEDATE__C', 'N/A')}")

        # Validate
        print(f"\nValidating with rules from 'validation_rules.json'...")
        validator = JSONValidator('validation_rules.json')
        warnings, errors = validator.validate(loan_terms)

        # Format results as JSON
        print(f"\n{'='*70}")
        print(f"Validation Results")
        print(f"{'='*70}\n")

        result = {
            "LOAN_NAME": loan_terms['NAME'],
            "LOAN_ID": loan_terms['ID'],
            "WARNINGS": warnings,
            "ERRORS": errors
        }

        print(json.dumps(result, indent=4))

        # Summary
        print(f"\n{'='*70}")
        if errors:
            print(f"❌ {len(errors)} error(s) found")
        else:
            print("✓ NO ERRORS")

        if warnings:
            print(f"⚠️  {len(warnings)} warning(s) found")
        else:
            print("✓ NO WARNINGS")
        print(f"{'='*70}\n")

    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
