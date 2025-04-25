from string import Template

JD_TEMPLATE = Template('''
# **$role_title**
**Location:** $location  
**Employment Type:** $employment_type

---

## **About the Company**
$company_intro

---

## **Role Overview**
$role_overview

---

## **Key Responsibilities**
$responsibilities

---

## **Qualifications & Skills**
$qualifications

---

## **What We Offer**
$benefits

---

## **Technical Environment**
$tech_environment

---

*We are an equal opportunity employer and value diversity. We do not discriminate based on race, religion, color, national origin, gender, sexual orientation, age, marital status, or disability status.*
''')

def format_list_items(items_list, paragraph_style=False):
    """Format a list of items into bullet points or paragraph"""
    if paragraph_style:
        return ", ".join([item for item in items_list if item.strip()])
    return "\n".join([f"- {item}" for item in items_list if item.strip()])

def format_tech_tools(tech_dict, paragraph_style=False):
    """Format technology and tools dictionary into categorized sections"""
    if paragraph_style:
        formatted = []
        for category, tools in tech_dict.items():
            if tools:
                formatted.append(f"**{category}:** {', '.join(tools)}")
        return " | ".join(formatted)
    else:
        formatted = []
        for category, tools in tech_dict.items():
            if tools:
                formatted.append(f"### **{category}**\n{', '.join(tools)}")
        return "\n\n".join(formatted)