import os, json, uuid, redis
r = redis.Redis.from_url(os.getenv("REDIS_URL"))

def enqueue_job(user_id, tool, args):
    job_id = str(uuid.uuid4())[:8]
    job = {"job_id":job_id,"user_id":user_id,"tool":tool,"args":args,"status":"queued","progress":0}
    r.lpush("job_queue", json.dumps(job))
    return job_id

def get_queue_position(job_id):
    items = r.lrange("job_queue",0,-1)
    for i,raw in enumerate(items):
        if json.loads(raw)["job_id"]==job_id:
            return len(items)-i
    return None
