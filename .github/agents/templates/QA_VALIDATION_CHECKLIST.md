# QA Validation Checklist

**Milestone**: [Milestone name/number]  
**Date**: [YYYY-MM-DD]  
**QA Agent Session**: [Session identifier]

---

## 1. Issue State Verification

### 1.1 Milestone Issues
- [ ] All milestone issues are closed
- [ ] Each issue has completion handoff comment
- [ ] Handoffs match actual deliverables
- [ ] No orphaned or incomplete work
- [ ] Issue descriptions reflect final implementation

### 1.2 Meta-Issue
- [ ] All sub-issues checked off
- [ ] Status reflects completion state
- [ ] Blockers section empty or resolved
- [ ] Acceptance criteria listed
- [ ] Known limitations documented

### 1.3 Traceability
- [ ] Commits reference issue numbers
- [ ] ADRs created for architectural changes
- [ ] Contract changes documented
- [ ] Breaking changes identified

### 1.4 Branch State
- [ ] All work committed and pushed
- [ ] No uncommitted changes
- [ ] Branch is mergeable with main
- [ ] No merge conflicts

**Issue State Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 2. System Runnable

### 2.1 Startup
- [ ] System can be started using documented commands
- [ ] Entry points work (Makefile, scripts, etc.)
- [ ] Required services come up cleanly
- [ ] No unexpected errors in startup logs

**Command Used**:
```bash
[startup command]
```

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

### 2.2 Configuration
- [ ] Configuration documented
- [ ] Environment variables clear
- [ ] Defaults sensible
- [ ] No hidden dependencies

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 3. End-to-End Flows

### Flow 1: [Flow name]
**Description**: [What this flow does]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected**: [Expected behavior]

**Actual**: [Actual behavior]

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

### Flow 2: [Flow name]
**Description**: [What this flow does]

**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected**: [Expected behavior]

**Actual**: [Actual behavior]

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 4. Documentation Accuracy

- [ ] README reflects current state
- [ ] User guide paths are real
- [ ] Architecture docs match implementation
- [ ] API/Interface docs accurate
- [ ] Troubleshooting section useful

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 5. Acceptance Criteria

**From Milestone Meta-Issue**:

- [ ] [Acceptance criterion 1]
- [ ] [Acceptance criterion 2]
- [ ] [Acceptance criterion 3]

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 6. Regression Check

- [ ] Existing functionality still works
- [ ] No unintended side effects
- [ ] Core flows unaffected
- [ ] Tests pass

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 7. Architectural Compliance

- [ ] Service boundaries respected
- [ ] Contracts honored
- [ ] No accidental tight coupling
- [ ] Architectural decisions documented

**Result**: ❌ FAIL / ⚠️ PARTIAL / ✅ PASS

---

## 8. Findings Summary

### Blocking Issues
[List any issues that prevent merge]

### Non-Blocking Concerns
[List minor issues or rough edges]

### Known Limitations
[List documented, acceptable limitations]

---

## 9. Overall Assessment

**Confidence Level**: ❌ LOW / ⚠️ MEDIUM / ✅ HIGH

**Recommendation**:
- [ ] ✅ APPROVE - Ready for PR creation and human review
- [ ] ⚠️ APPROVE WITH NOTES - Functional but has minor issues
- [ ] ❌ BLOCK - Does not meet acceptance criteria

**Justification**:
[Explain the recommendation]

---

## 10. PR Readiness

If APPROVED:
- [ ] All checklist items reviewed
- [ ] Issue state verified
- [ ] System validated end-to-end
- [ ] QA summary prepared
- [ ] Ready to create PR

**Next Action**: Create PR using `PULL_REQUEST_TEMPLATE.md`

---

## Notes

[Any additional context, observations, or recommendations]
