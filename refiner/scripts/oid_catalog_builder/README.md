# OID Catalog Builder

> [!NOTE]
> The markdown version of the eICR 3.1.1 IG was converted using `marker` to convert the PDF files to markdown.

In trying to keep many OIDs in place for entry matching rules in the eCR Refiner we ran into issues with small typos and other copy + paste issues. To get around this issue, we've put this script together to parse a markdown version of the eICR IG to pull out the human readable names in corresponding OID. The goal is that in authoring the rules in `entry_matching_rules.py` we can use the human readable name in the rule itself rather than an abstract OID that we can't check unless we have the IG open. This should hopefully prevent both typos at the OID level and also whether or not we're targeting the right thing with the correct human name.

To update the `template_oids.py` script run this in the `scripts/oid_catalog_builder/`:

```bash
./generate_template_oids.sh
```

There may be a `ruff` issue that you can quickly fix if present but otherwise don't edit this doc by hand.
