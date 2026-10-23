from pathlib import Path
import json
import pipeline
root=pipeline.ROOT
jobs=pipeline.read(root/'source/scripts/jobs.json');anchors=pipeline.read(root/'source/scripts/anchors.json')
for job in jobs:
 job.update(anchors.get(job['id'],{}));pipeline.ingest(job)
pipeline.write(root/'source/scripts/jobs.json',jobs)
print('Reprocessed',len(jobs),'assets with recorded manual landmarks.')
