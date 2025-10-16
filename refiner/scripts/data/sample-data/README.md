# Sample Data By Jurisdiction

The script in this directory is used to create copies of the sample file provided by the eCR Refiner team that have been modified to work on a per-jurisdiction basis.

After running the script the `jurisdiction_sample_data` directory  will contain a testing file for every jurisdiction listed in the `eCR_Jurisdictions.csv` file, plus a few additional "jurisdictions" (`APHL`, `CDC`, and `TEST`).

## Generating Sample Data

```sh
python create_sample_data_by_jd.py
```
