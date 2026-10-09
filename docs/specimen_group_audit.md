# Pilot specimen grouping review

The pinned mirror's `texture_list.xlsx` identifies the selected specimens as Nyatoh (0), granite (38), high-density polyethylene (49), stainless steel (65), float glass (74), linoleum (79), alumina (82), jute (87), velvet (102), corduroy (103), poplar (10), and PET (57). IDs 10 and 57 remain provisional development validation specimens.

The selected names contain no obvious duplicate material family across train and validation. Broad categories such as wood or polymer are not automatically treated as one family. Polyethylene and glass finishes receive explicit grouping labels so that closely named variants must share a split if added later. This is a review of the available specimen names, recorded in `configs/pilot_groups.csv` with scope `metadata_names_only`.

Manufacturing lot, supplier, weave/fiber composition, and relationships between the fabric specimens are not established by these names. A true review flag means the stated metadata review was completed; it does not establish independent manufacturing families. Before selecting a scientific test, review the complete specimen list and any available fabrication information, then freeze the grouping manifest. Adding surfaces requires explicit review entries; shared family labels crossing the split are rejected.

Source: mirror revision `b7c2fb70ed2d68219389478660f35c2cd49c69fb`, hashed locally in the raw inventory. The [authors' dataset documentation](https://github.com/cluster-lab/Cluster-Haptic-Texture-Dataset/blob/main/documents/dataset_details.md) describes the specimen metadata and recording naming scheme. The CSV contents are hashed into the expanded pilot configuration.
