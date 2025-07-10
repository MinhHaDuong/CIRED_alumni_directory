#!/usr/bin/env python3
"""Test script to verify organization deduplication works correctly"""

import vobject
import sys
import os

# Add the project root and 4_Clean directory to the path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '4_Clean'))

from utils import TypedVCard
import clean

def create_test_vcard(org_values: list[str]) -> TypedVCard:
    """Create a test vCard with the given organization values"""
    vcard = vobject.vCard()
    vcard.add('fn').value = 'Test Person'
    
    for org_value in org_values:
        vcard.add('org').value = org_value
    
    return vcard  # TypedVCard is just a protocol, so we can return the vCard directly

def test_within_line_deduplication():
    """Test that within-line duplicates are properly handled"""
    test_cases = [
        # Test repeated words
        (["CIRED CIRED"], ["CIRED"]),
        (["CIRED cired"], ["CIRED"]),  # Case insensitive
        (["CIRED CIRED University"], ["CIRED University"]),
        
        # Test comma-separated duplicates
        (["CIRED, CIRED"], ["CIRED"]),
        (["CIRED, cired, University"], ["CIRED, University"]),
        
        # Test semicolon-separated duplicates
        (["CIRED; CIRED"], ["CIRED"]),
        (["CIRED; University; CIRED"], ["CIRED; University"]),
        
        # Test mixed cases
        (["Centre International de Recherche sur l'Environnement et le Développement CIRED"], ["CIRED"]),
        (["CIRED, Centre International de Recherche sur l'Environnement et le Développement"], ["CIRED"]),
        
        # Test no duplicates (should remain unchanged)
        (["CIRED University"], ["CIRED University"]),
        (["CIRED, University"], ["CIRED, University"]),
    ]
    
    print("Testing within-line organization deduplication:")
    print("=" * 60)
    
    for i, (input_orgs, expected_orgs) in enumerate(test_cases, 1):
        vcard = create_test_vcard(input_orgs)
        print(f"\nTest {i}:")
        print(f"Input:    {input_orgs}")
        
        deduplicate_CIRED_ORG(vcard)
        
        actual_orgs = [str(org.value) for org in vcard.contents.get('org', [])]
        print(f"Output:   {actual_orgs}")
        print(f"Expected: {expected_orgs}")
        
        if actual_orgs == expected_orgs:
            print("✓ PASS")
        else:
            print("✗ FAIL")
    
    print("\n" + "=" * 60)

def test_across_line_deduplication():
    """Test that across-line duplicates are properly handled"""
    test_cases = [
        # Multiple identical organizations
        (["CIRED", "CIRED"], ["CIRED"]),
        (["CIRED", "cired"], ["CIRED"]),  # Case insensitive
        
        # Full name normalization + deduplication
        (["Centre International de Recherche sur l'Environnement et le Développement", "CIRED"], ["CIRED"]),
        
        # Mixed with other organizations
        (["CIRED", "University of Paris", "CIRED"], ["CIRED", "University of Paris"]),
    ]
    
    print("\nTesting across-line organization deduplication:")
    print("=" * 60)
    
    for i, (input_orgs, expected_orgs) in enumerate(test_cases, 1):
        vcard = create_test_vcard(input_orgs)
        print(f"\nTest {i}:")
        print(f"Input:    {input_orgs}")
        
        deduplicate_CIRED_ORG(vcard)
        
        actual_orgs = [str(org.value) for org in vcard.contents.get('org', [])]
        print(f"Output:   {actual_orgs}")
        print(f"Expected: {expected_orgs}")
        
        if set(actual_orgs) == set(expected_orgs) and len(actual_orgs) == len(expected_orgs):
            print("✓ PASS")
        else:
            print("✗ FAIL")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_within_line_deduplication()
    test_across_line_deduplication()
