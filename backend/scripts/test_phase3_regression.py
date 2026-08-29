import pytest
from app.analysis.models.base import AnalysisEvidence, EvidenceType
from app.analysis.models.project_models import ProjectEvidence
from app.analysis.engines.scoring.competency_scoring import get_derived_competency_contributions, score_competency, calculate_placement_signals
from app.analysis.engines.scoring.technology_scoring import score_technology

def test_foundational_tech_propagation_regression_a():
    # Built CNN using TensorFlow.
    # Expected: TensorFlow > 80, Python > 50, ML competency > 50
    evidences_a = [AnalysisEvidence(evidence_text="Built CNN using TensorFlow.", source_section="projects", validated=True)]
    
    tf_score = score_technology(evidences_a)
    assert tf_score >= 80.0
    
    # Python competency comes from derived contribution of TensorFlow
    derived = get_derived_competency_contributions(["TensorFlow"])
    py_contrib = derived.get("python", 0.0)
    assert py_contrib > 0.0
    
    py_score = score_competency("Python", [], py_contrib)
    assert py_score > 50.0
    
    ml_contrib = derived.get("machine_learning", 0.0)
    ml_score = score_competency("Machine Learning", [], ml_contrib)
    assert ml_score > 50.0

def test_foundational_tech_propagation_regression_b():
    # Implemented backend APIs in Python.
    # Expected: Python > 80, TensorFlow == 0, ML competency == 0
    evidences_b = [AnalysisEvidence(evidence_text="Implemented backend APIs in Python.", source_section="projects", validated=True)]
    
    py_score = score_technology(evidences_b)
    assert py_score >= 80.0
    
    derived = get_derived_competency_contributions(["Python"])
    tf_contrib = derived.get("tensorflow", 0.0)
    assert tf_contrib == 0.0
    
    ml_contrib = derived.get("machine_learning", 0.0)
    assert ml_contrib == 0.0

def test_foundational_tech_propagation_regression_c():
    # Built CNN using TensorFlow and Keras. Trained models in Python. Achieved 94% accuracy.
    # Expected: TensorFlow > 80, Python > 70, Machine Learning signal > 0, Deep Learning signal > 0
    ev_tf = AnalysisEvidence(evidence_text="Built CNN using TensorFlow and Keras.", source_section="projects", validated=True)
    ev_py = AnalysisEvidence(evidence_text="Trained models in Python.", source_section="projects", validated=True)
    ev_res = AnalysisEvidence(evidence_text="Achieved 94% accuracy.", source_section="projects", validated=True)
    
    tf_score = score_technology([ev_tf], has_results=True)
    assert tf_score >= 80.0
    
    derived = get_derived_competency_contributions(["TensorFlow", "Keras", "Python"])
    py_contrib = derived.get("python", 0.0)
    py_score = score_competency("Python", [ev_py], py_contrib)
    
    assert py_score >= 70.0
    
    signals = calculate_placement_signals(["TensorFlow", "Keras", "Python"])
    assert signals.get("machine_learning", 0.0) > 0.0
    assert signals.get("deep_learning", 0.0) > 0.0
