from trytond.pool import Pool
from . import admin_profile
from . import specialty_area


def register():
    Pool.register(
        admin_profile.AdminProfile,
        admin_profile.AdminProfileGroup,
        admin_profile.AdminProfileLog,
        admin_profile.AdminProfileLogGroupAdded,
        admin_profile.AdminProfileLogGroupRemoved,
        admin_profile.ApplyProfileStart,
        specialty_area.SpecialtyArea,
        specialty_area.SpecialtyAreaGroup,
        specialty_area.SpecialtyAreaSpecialty,
        specialty_area.ApplySpecialtyStart,
        module='health_admin_profiles', type_='model')
    Pool.register(
        admin_profile.User,
        specialty_area.Specialty,
        specialty_area.HealthProfessional,
        module='health_admin_profiles', type_='model')
    Pool.register(
        admin_profile.ApplyProfile,
        specialty_area.ApplySpecialty,
        module='health_admin_profiles', type_='wizard')
