"""Access control tools (users, groups, ACL, tokens)."""
from typing import List, Optional
from mcp.types import TextContent as Content
from .base import ProxmoxTool


class AccessTools(ProxmoxTool):
    """Users, groups, roles, ACL, and API tokens."""

    def list_users(self) -> List[Content]:
        try:
            users = self.proxmox.access.users.get()
            return self._format_response(users)
        except Exception as e:
            self._handle_error("list users", e)

    def get_user(self, userid: str) -> List[Content]:
        try:
            user = self.proxmox.access.users(userid).get()
            return self._format_response(user)
        except Exception as e:
            self._handle_error(f"get user {userid}", e)

    def create_user(
        self,
        userid: str,
        password: Optional[str] = None,
        comment: Optional[str] = None,
        email: Optional[str] = None,
        enable: bool = True,
    ) -> List[Content]:
        try:
            params = {"userid": userid, "enable": 1 if enable else 0}
            if password is not None:
                params["password"] = password
            if comment is not None:
                params["comment"] = comment
            if email is not None:
                params["email"] = email
            result = self.proxmox.access.users.post(**params)
            return [Content(type="text", text=f"User '{userid}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create user {userid}", e)

    def delete_user(self, userid: str) -> List[Content]:
        try:
            result = self.proxmox.access.users(userid).delete()
            return [Content(type="text", text=f"User '{userid}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete user {userid}", e)

    def list_groups(self) -> List[Content]:
        try:
            groups = self.proxmox.access.groups.get()
            return self._format_response(groups)
        except Exception as e:
            self._handle_error("list groups", e)

    def create_group(self, groupid: str, comment: Optional[str] = None) -> List[Content]:
        try:
            params = {"groupid": groupid}
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.access.groups.post(**params)
            return [Content(type="text", text=f"Group '{groupid}' created\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"create group {groupid}", e)

    def delete_group(self, groupid: str) -> List[Content]:
        try:
            result = self.proxmox.access.groups(groupid).delete()
            return [Content(type="text", text=f"Group '{groupid}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete group {groupid}", e)

    def list_roles(self) -> List[Content]:
        try:
            roles = self.proxmox.access.roles.get()
            return self._format_response(roles)
        except Exception as e:
            self._handle_error("list roles", e)

    def list_acl(self) -> List[Content]:
        try:
            acl = self.proxmox.access.acl.get()
            return self._format_response(acl)
        except Exception as e:
            self._handle_error("list ACL", e)

    def update_acl(
        self,
        path: str,
        roles: str,
        users: Optional[str] = None,
        groups: Optional[str] = None,
        propagate: bool = True,
        delete: bool = False,
    ) -> List[Content]:
        try:
            params = {
                "path": path,
                "roles": roles,
                "propagate": 1 if propagate else 0,
            }
            if users is not None:
                params["users"] = users
            if groups is not None:
                params["groups"] = groups
            if delete:
                params["delete"] = 1
            result = self.proxmox.access.acl.put(**params)
            action = "removed" if delete else "updated"
            return [Content(type="text", text=f"ACL {action} for path '{path}'\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"update ACL for {path}", e)

    def list_tokens(self, userid: str) -> List[Content]:
        try:
            tokens = self.proxmox.access.users(userid).token.get()
            return self._format_response(tokens)
        except Exception as e:
            self._handle_error(f"list tokens for {userid}", e)

    def create_token(
        self,
        userid: str,
        tokenid: str,
        comment: Optional[str] = None,
        privsep: bool = True,
    ) -> List[Content]:
        try:
            params = {"privsep": 1 if privsep else 0}
            if comment is not None:
                params["comment"] = comment
            result = self.proxmox.access.users(userid).token(tokenid).post(**params)
            # Token secret is returned once — include in response for the caller; never log it
            self.logger.info(
                "API token created for user %s id %s (secret returned to caller once; not logged)",
                userid,
                tokenid,
            )
            return [
                Content(
                    type="text",
                    text=(
                        f"API token '{userid}!{tokenid}' created.\n"
                        "⚠️ SECURITY: Store the secret now; Proxmox shows it only once. "
                        "Do not paste it into chat logs or commit it to git.\n"
                        f"Result: {result}"
                    ),
                )
            ]
        except Exception as e:
            self._handle_error(f"create token {userid}!{tokenid}", e)

    def delete_token(self, userid: str, tokenid: str) -> List[Content]:
        try:
            result = self.proxmox.access.users(userid).token(tokenid).delete()
            return [Content(type="text", text=f"Token '{userid}!{tokenid}' deleted\nResult: {result}")]
        except Exception as e:
            self._handle_error(f"delete token {userid}!{tokenid}", e)

    def get_permissions(self) -> List[Content]:
        try:
            perms = self.proxmox.access.permissions.get()
            return self._format_response(perms)
        except Exception as e:
            self._handle_error("get permissions", e)

    def get_token_permissions(self, userid: str, tokenid: str) -> List[Content]:
        """Get effective permissions for a privilege-separated API token.

        Pass userid as user@realm (e.g. mcp@pve) and tokenid as the token name.
        Proxmox identity becomes user@realm!tokenid — required when privsep=Yes (D8).
        """
        try:
            token_userid = f"{userid}!{tokenid}"
            perms = self.proxmox.access.permissions.get(userid=token_userid)
            meta = {
                "userid": userid,
                "tokenid": tokenid,
                "token_identity": token_userid,
                "hint": (
                    "If this map is empty/near-empty with Privilege Separation=Yes, "
                    "grant ACLs to the token identity (user@realm!tokenid), not only the user."
                ),
                "permissions": perms,
            }
            return self._format_response(meta)
        except Exception as e:
            self._handle_error(f"get token permissions for {userid}!{tokenid}", e)
