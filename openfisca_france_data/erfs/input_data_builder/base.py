def year_specific_by_generic_data_frame_name(year):
    yr = str(year)[2:]
    yr1 = str(year + 1)[2:]
    return dict(
        # Enquête revenu fiscaux, table ménage
        erf_menage = "menage" + yr,
        # Enquête emploi en continu, table ménage
        eec_menage = "mrf" + yr + "e" + yr + "t4",
        # Enquête revenu fiscaux, table foyer # compressed file for 2006
        foyer = "foyer" + yr,
        # Enquête revenu fiscaux, table individu
        erf_indivi = "indivi{}".format(yr),
        # Enquête emploi en continue, table individu
        eec_indivi = "irf" + yr + "e" + yr + "t4",
        # Enquête emploi en continue, tables complémentaires 1
        eec_cmp_1 = "icomprf" + yr + "e" + yr1 + "t1",
        eec_cmp_2 = "icomprf" + yr + "e" + yr1 + "t2",
        eec_cmp_3 = "icomprf" + yr + "e" + yr1 + "t3",
        )
