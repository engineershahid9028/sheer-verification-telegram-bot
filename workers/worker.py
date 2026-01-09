import os, json, redis, subprocess
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

while True:
    raw = r.brpop("job_queue")[1]
    job = json.loads(raw)
    tool = job["tool"]
    args = job["args"]
    p = subprocess.Popen(["python", f"tools/multi-tools/{tool}/main.py"] + args.split(),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    r.hset(job["job_id"], mapping={"status":"done","output":(out+err).decode(),"progress":100})
