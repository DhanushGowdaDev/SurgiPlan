from data.models import Surgery, OperatingRoom, Staff, Equipment, RecoveryBed


def create_surgeries():
    return [
        Surgery(
            "S101", "Emergency Appendectomy", "General Surgery",
            "Emergency", 90, "Dr. Sharma", "Dr. Kumar",
            ["General Surgical Set"], 1
        ),
        Surgery(
            "S102", "Emergency Trauma Surgery", "Trauma",
            "Emergency", 120, "Dr. Rao", "Dr. Mehta",
            ["C-Arm"], 2
        ),

        Surgery(
            "S103", "Hip Replacement", "Orthopedics",
            "Critical", 150, "Dr. Patel", "Dr. Kumar",
            ["C-Arm"], 2
        ),
        Surgery(
            "S104", "Cardiac Bypass", "Cardiology",
            "Critical", 240, "Dr. Menon", "Dr. Singh",
            ["Cardiac Bypass Machine"], 3
        ),
        Surgery(
            "S105", "Brain Tumor Surgery", "Neurosurgery",
            "Critical", 210, "Dr. Iyer", "Dr. Mehta",
            ["Surgical Robot"], 2
        ),
        Surgery(
            "S106", "Spinal Fusion", "Orthopedics",
            "Critical", 180, "Dr. Patel", "Dr. Singh",
            ["C-Arm"], 2
        ),

        Surgery(
            "S107", "Knee Replacement", "Orthopedics",
            "High", 120, "Dr. Patel", "Dr. Kumar",
            ["C-Arm"], 1
        ),
        Surgery(
            "S108", "Gallbladder Surgery", "General Surgery",
            "High", 90, "Dr. Sharma", "Dr. Mehta",
            ["General Surgical Set"], 1
        ),
        Surgery(
            "S109", "Lung Resection", "Thoracic",
            "High", 180, "Dr. Reddy", "Dr. Singh",
            ["Surgical Robot"], 2
        ),
        Surgery(
            "S110", "Kidney Surgery", "Urology",
            "High", 150, "Dr. Joshi", "Dr. Kumar",
            ["Endoscopy Tower"], 1
        ),
        Surgery(
            "S111", "Endoscopy", "Gastroenterology",
            "High", 60, "Dr. Rao", "Dr. Mehta",
            ["Endoscopy Tower"], 1
        ),
        Surgery(
            "S112", "Laser Eye Surgery", "Ophthalmology",
            "High", 60, "Dr. Kapoor", "Dr. Singh",
            ["Laser System"], 1
        ),

        Surgery(
            "S113", "Hernia Repair", "General Surgery",
            "Normal", 75, "Dr. Sharma", "Dr. Kumar",
            ["General Surgical Set"], 1
        ),
        Surgery(
            "S114", "Thyroid Surgery", "General Surgery",
            "Normal", 90, "Dr. Reddy", "Dr. Mehta",
            ["General Surgical Set"], 1
        ),
        Surgery(
            "S115", "Cataract Surgery", "Ophthalmology",
            "Normal", 45, "Dr. Kapoor", "Dr. Singh",
            ["Laser System"], 1
        ),
        Surgery(
            "S116", "Arthroscopy", "Orthopedics",
            "Normal", 90, "Dr. Patel", "Dr. Kumar",
            ["C-Arm"], 1
        ),
        Surgery(
            "S117", "Prostate Surgery", "Urology",
            "Normal", 120, "Dr. Joshi", "Dr. Mehta",
            ["Endoscopy Tower"], 1
        ),
        Surgery(
            "S118", "Liver Surgery", "General Surgery",
            "Normal", 180, "Dr. Menon", "Dr. Singh",
            ["Surgical Robot"], 2
        ),

        Surgery(
            "S119", "Minor Skin Surgery", "Dermatology",
            "Low", 45, "Dr. Iyer", "Dr. Kumar",
            ["General Surgical Set"], 1
        ),
        Surgery(
            "S120", "Biopsy Procedure", "General Surgery",
            "Low", 30, "Dr. Reddy", "Dr. Mehta",
            ["General Surgical Set"], 1
        ),
    ]


def create_operating_rooms():
    return [
        OperatingRoom(
            "OR-1",
            ["General Surgery", "Trauma", "Gastroenterology"]
        ),
        OperatingRoom(
            "OR-2",
            ["Orthopedics", "Trauma"]
        ),
        OperatingRoom(
            "OR-3",
            ["Cardiology", "Thoracic"]
        ),
        OperatingRoom(
            "OR-4",
            ["Neurosurgery", "Ophthalmology"]
        ),
        OperatingRoom(
            "OR-5",
            ["Urology", "General Surgery", "Ophthalmology"]
        ),
    ]


def create_staff():
    surgeons = [
        "Dr. Sharma",
        "Dr. Rao",
        "Dr. Patel",
        "Dr. Menon",
        "Dr. Iyer",
        "Dr. Reddy",
        "Dr. Joshi",
        "Dr. Kapoor",
        "Dr. Verma",
        "Dr. Nair",
    ]

    anesthetists = [
        "Dr. Kumar",
        "Dr. Mehta",
        "Dr. Singh",
        "Dr. Thomas",
        "Dr. Shah",
    ]

    nurses = [
        "Nurse Asha",
        "Nurse Priya",
        "Nurse Kavya",
        "Nurse Anu",
        "Nurse Divya",
        "Nurse Sneha",
        "Nurse Riya",
        "Nurse Pooja",
        "Nurse Neha",
        "Nurse Meera",
    ]

    staff = []

    for surgeon in surgeons:
        staff.append(Staff(surgeon, "surgeon"))

    for anesthetist in anesthetists:
        staff.append(Staff(anesthetist, "anesthetist"))

    for nurse in nurses:
        staff.append(Staff(nurse, "nurse"))

    return staff


def create_equipment():
    equipment = [
        ("EQ-01", "Surgical Robot"),
        ("EQ-02", "Surgical Robot"),
        ("EQ-03", "C-Arm"),
        ("EQ-04", "C-Arm"),
        ("EQ-05", "Endoscopy Tower"),
        ("EQ-06", "Endoscopy Tower"),
        ("EQ-07", "Laser System"),
        ("EQ-08", "Laser System"),
        ("EQ-09", "Cardiac Bypass Machine"),
        ("EQ-10", "General Surgical Set"),
    ]

    return [
        Equipment(equipment_id, equipment_type)
        for equipment_id, equipment_type in equipment
    ]


def create_recovery_beds():
    return [
        RecoveryBed(f"BED-{i:02d}")
        for i in range(1, 16)
    ]


def create_demo_data():
    return {
        "surgeries": create_surgeries(),
        "operating_rooms": create_operating_rooms(),
        "staff": create_staff(),
        "equipment": create_equipment(),
        "recovery_beds": create_recovery_beds(),
    }