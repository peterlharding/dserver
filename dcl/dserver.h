
#ifndef _DSERVER_H_
#define _DSERVER_H_

//-------------------------------------------------------------------------------------------------

#define PORT        9572
#define HOST        "localhost"
#define SERVICE     "dserver"

//-----------------------------------------------------------------------------

typedef void* DS_SESSION;

//-------------------------------------------------------------------------------------------------

extern DS_SESSION   * dsInit(char *host, int port);
extern int            dsRegister(DS_SESSION *session, char *data_source);
extern char         * dsGetNext(DS_SESSION *session, int handle);
extern char         * dsGetKeyed(DS_SESSION *session, int handle, char *group);
extern char         * dsGetIndexed(DS_SESSION *session, int handle, char *group);
extern char         * dsStore(DS_SESSION *session, int handle, char* data);
extern char         * dsStoreKeyed(DS_SESSION *session, int handle, char *group, char *data);

//-------------------------------------------------------------------------------------------------

#endif // _DSERVER_H
