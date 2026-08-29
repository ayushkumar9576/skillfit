import { 
  CandidateIntelligenceProfile, 
  DemonstrationLevel,
  VerificationStatus,
  IntelligenceSourceType,
  OwnershipLevel,
  FindingType,
  FindingSeverity,
  EngineeringSignalCategory,
  DomainType
} from "@/types/candidate-profile";

export const mockCandidateProfile: CandidateIntelligenceProfile = {
  metadata: {
    total_projects_analyzed: 4,
    total_internships_analyzed: 1,
    total_certifications_analyzed: 0,
    analysis_version: "3.1.0"
  },
  summary: {
    primary_domains: [DomainType.MACHINE_LEARNING, DomainType.BACKEND],
    strongest_competencies: ["Machine Learning", "API Design", "Problem Solving"],
    strongest_technologies: ["Python", "TensorFlow", "FastAPI"],
    largest_gaps: ["Testing Frameworks", "CI/CD Pipelines"],
    readiness_highlights: [
      "Demonstrated ability to deploy ML models via APIs.",
      "Lacks enterprise testing rigor."
    ]
  },
  technologies: [
    {
      technology: "Python",
      demonstration_level: DemonstrationLevel.IMPLEMENTED,
      source_types: [IntelligenceSourceType.PROJECT, IntelligenceSourceType.INTERNSHIP],
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Built CNN training pipeline in Python using TensorFlow.",
          line_reference: 12
        }
      ]
    },
    {
      technology: "TensorFlow",
      demonstration_level: DemonstrationLevel.IMPLEMENTED,
      source_types: [IntelligenceSourceType.PROJECT],
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Designed model architecture in TensorFlow.",
          line_reference: 13
        }
      ]
    },
    {
      technology: "Docker",
      demonstration_level: DemonstrationLevel.CLAIMED,
      source_types: [IntelligenceSourceType.SELF_REPORTED],
      evidence: [
        {
          source: IntelligenceSourceType.SELF_REPORTED,
          source_id: "Skills Section",
          section: "Skills",
          quote: "Skills: Python, TensorFlow, Docker, AWS",
          line_reference: 30
        }
      ]
    }
  ],
  competencies: [
    {
      competency: "Machine Learning",
      demonstrated: true,
      demonstration_level: DemonstrationLevel.IMPLEMENTED,
      supporting_technologies: ["Python", "TensorFlow", "Scikit-Learn"],
      supporting_projects: ["AI Resume Analyzer"],
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Trained and deployed a text classification model.",
          line_reference: 14
        }
      ]
    },
    {
      competency: "Backend API Development",
      demonstrated: true,
      demonstration_level: DemonstrationLevel.USED,
      supporting_technologies: ["FastAPI"],
      supporting_projects: ["E-commerce API"],
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "E-commerce API",
          section: "Projects",
          quote: "Exposed predictions via FastAPI endpoints.",
          line_reference: 18
        }
      ]
    }
  ],
  skills: [
    {
      skill: "Model Training",
      verification_status: VerificationStatus.STRONGLY_VERIFIED,
      demonstration_level: DemonstrationLevel.IMPLEMENTED,
      evidence_count: 3,
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Trained and deployed a text classification model.",
          line_reference: 14
        }
      ]
    },
    {
      skill: "Cloud Deployment",
      verification_status: VerificationStatus.UNVERIFIED,
      demonstration_level: DemonstrationLevel.CLAIMED,
      evidence_count: 0,
      evidence: []
    }
  ],
  domains: [
    {
      domain: DomainType.MACHINE_LEARNING,
      supporting_competencies: ["Model Training", "Data Processing"],
      supporting_technologies: ["Python", "TensorFlow"],
      evidence: []
    }
  ],
  certifications: [],
  ownership_signals: [
    {
      signal: "Project Architecture",
      ownership_level: OwnershipLevel.OWNED,
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Solo developer, architected the entire data pipeline.",
          line_reference: 11
        }
      ]
    }
  ],
  engineering_signals: [
    {
      category: EngineeringSignalCategory.DEPLOYMENT,
      signal: "Containerization",
      demonstrated: true,
      evidence: [
        {
          source: IntelligenceSourceType.INTERNSHIP,
          source_id: "Software Engineering Intern",
          section: "Experience",
          quote: "Packaged backend microservices into Docker containers.",
          line_reference: 5
        }
      ]
    },
    {
      category: EngineeringSignalCategory.TESTING,
      signal: "Unit Testing",
      demonstrated: false,
      evidence: []
    }
  ],
  workplace_exposure: [
    {
      exposure_type: "Agile Development",
      evidence: [
        {
          source: IntelligenceSourceType.INTERNSHIP,
          source_id: "Software Engineering Intern",
          section: "Experience",
          quote: "Participated in daily standups and two-week sprints.",
          line_reference: 7
        }
      ]
    }
  ],
  findings: [
    {
      title: "Missing Testing Evidence",
      type: FindingType.MISSING_SIGNAL,
      severity: FindingSeverity.HIGH,
      description: "No testing frameworks (e.g. pytest, jest) detected in any project or internship.",
      evidence: []
    },
    {
      title: "Strong ML Portfolio",
      type: FindingType.STRENGTH,
      severity: FindingSeverity.LOW,
      description: "Multiple projects demonstrate end-to-end ML model development.",
      evidence: [
        {
          source: IntelligenceSourceType.PROJECT,
          source_id: "AI Resume Analyzer",
          section: "Projects",
          quote: "Trained and deployed a text classification model.",
          line_reference: 14
        }
      ]
    }
  ],
  recommendations: [
    {
      title: "Add Unit Tests",
      description: "Add pytest to your AI Resume Analyzer to prove testing competency.",
      priority: "HIGH",
      estimated_impact: "High",
      target_competencies: ["Software Testing"],
      derived_from: ["Missing Testing Evidence"]
    }
  ]
};

export const mockReadinessResult = {
  readiness_level: "READY",
  summary_text: "Candidate demonstrates strong implementation, deployment, and ownership signals in backend and machine learning.",
  strength_areas: [
    "Production-grade ML pipeline implementation",
    "Strong ownership of system architecture",
    "Consistent usage of testing methodologies"
  ],
  improvement_areas: [
    "Limited exposure to enterprise cloud environments (AWS/Azure)",
    "Missing security implementation signals"
  ]
};
